import os
import csv
import copy
import argparse
import concurrent.futures
import hydra
from faker import Faker
from datetime import datetime
from omegaconf import OmegaConf, DictConfig
from DrissionPage import ChromiumOptions, Chromium

from temp_mails import Tempmail_io, Guerillamail_com
from helper.cursor_register import CursorRegister
from helper.email import *

# Parameters for debugging purpose
hide_account_info = os.getenv('HIDE_ACCOUNT_INFO', 'false').lower() == 'true'
enable_headless = os.getenv('ENABLE_HEADLESS', 'false').lower() == 'true'
enable_browser_log = os.getenv('ENABLE_BROWSER_LOG', 'true').lower() == 'true' or not enable_headless

def register_cursor_core(register_config, options):

    try:
        # Maybe fail to open the browser
        browser = Chromium(options)
    except Exception as e:
        print(e)
        return None
    
    if register_config.email_server.name == "temp_email_server":
        email_server = eval(register_config.temp_email_server.name)(browser)
        email_address = email_server.get_email_address()
    elif register_config.email_server.name == "imap_email_server":
        imap_server = register_config.imap_email_server.imap_server
        imap_port = register_config.imap_email_server.imap_port
        imap_username = register_config.imap_email_server.username
        imap_password = register_config.imap_email_server.password
        email_address = register_config.email_server.email_address
        email_server = Imap(imap_server, imap_port, imap_username, imap_password, email_to = email_address)

    register = CursorRegister(browser, email_server)
    tab_signin, status = register.sign_in(email_address)
    #tab_signup, status = register.sign_up(email_address)
    token = register.get_cursor_cookie(tab_signin)

    if token is not None:
        user_id = token.split("%3A%3A")[0]
        delete_low_balance_account = register_config.delete_low_balance_account
        if register_config.email_server.name == "imap_email_server" and delete_low_balance_account:
            delete_low_balance_account_threshold = register_config.delete_low_balance_account_threshold

            usage = register.get_usage(user_id)
            balance = usage["gpt-4"]["maxRequestUsage"] - usage["gpt-4"]["numRequests"]
            if balance < delete_low_balance_account_threshold:
                register.delete_account()
                tab_signin, status = register.sign_in(email_address)
                token = register.get_cursor_cookie(tab_signin)

    if status or not enable_browser_log:
        register.browser.quit(force=True, del_data=True)

    if status and not hide_account_info:
        print(f"[Register] Cursor Email: {email_address}")
        print(f"[Register] Cursor Token: {token}")

    ret = {
        "username": email_address,
        "token": token
    }

    return ret

def register_cursor(register_config):

    options = ChromiumOptions()
    options.auto_port()
    options.new_env()
    # Use turnstilePatch from https://github.com/TheFalloutOf76/CDP-bug-MouseEvent-.screenX-.screenY-patcher
    turnstile_patch_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "turnstilePatch"))
    options.add_extension(turnstile_patch_path)

    # If fail to pass the cloudflare in headless mode, try to align the user agent with your real browser
    if enable_headless: 
        from platform import platform
        if platform == "linux" or platform == "linux2":
            platformIdentifier = "X11; Linux x86_64"
        elif platform == "darwin":
            platformIdentifier = "Macintosh; Intel Mac OS X 10_15_7"
        elif platform == "win32":
            platformIdentifier = "Windows NT 10.0; Win64; x64"
        # Please align version with your Chrome
        chrome_version = "130.0.0.0"        
        options.set_user_agent(f"Mozilla/5.0 ({platformIdentifier}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36")
        options.headless()

    number = register_config.number
    max_workers = register_config.max_workers
    print(f"[Register] Start to register {number} accounts in {max_workers} threads")

    # Run the code using multithreading
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for idx in range(number):
            register_config_thread = copy.deepcopy(register_config)
            use_custom_address = register_config.email_server.use_custom_address
            custom_email_address = register_config.email_server.custom_email_address
            register_config_thread.email_server.email_address = custom_email_address[idx] if use_custom_address else None
            options_thread = copy.deepcopy(options)
            futures.append(executor.submit(register_cursor_core, register_config_thread, options_thread))
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result is not None:
                results.append(result)

    results = [result for result in results if result["token"] is not None]

    if len(results) > 0:
        formatted_date = datetime.now().strftime("%Y-%m-%d")

        fieldnames = results[0].keys()
        # Write username, token into a csv file
        with open(f"./output_{formatted_date}.csv", 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writerows(results)
        # Only write token to csv file, without header
        tokens = [{'token': row['token']} for row in results]
        with open( f"./token_{formatted_date}.csv", 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['token'])
            writer.writerows(tokens)

    return results

@hydra.main(config_path="config", config_name="config", version_base=None)
def main(config: DictConfig):
    OmegaConf.set_struct(config, False)
    # Validate the config
    email_server_name = config.register.email_server.name
    use_custom_address = config.register.email_server.use_custom_address
    custom_email_address = config.register.email_server.custom_email_address
    assert email_server_name in ["temp_email_server", "imap_email_server"], "email_server_name should be either temp_email_server or imap_email_server"
    assert use_custom_address and email_server_name == "imap_email_server" or not use_custom_address, "use_custom_address should be True only when email_server_name is imap_email_server"
    if use_custom_address and email_server_name == "imap_email_server":
        config.register.number = len(custom_email_address)
        print(f"[Register] Parameter regitser.number is overwritten by the length of custom_email_address: {len(custom_email_address)}")
    

    account_infos = register_cursor(config.register)
    tokens = list(set([row['token'] for row in account_infos]))
    print(f"[Register] Register {len(tokens)} accounts successfully")
    
    if config.oneapi.enabled and len(account_infos) > 0:
        from tokenManager.oneapi_manager import OneAPIManager
        from tokenManager.cursor import Cursor

        oneapi_url = config.oneapi.url
        oneapi_token = config.oneapi.token
        oneapi_channel_url = config.oneapi.channel_url

        oneapi = OneAPIManager(oneapi_url, oneapi_token)
        # Send request by batch to avoid "Too many SQL variables" error in SQLite.
        # If you use MySQL, better to set the batch_size as len(tokens)
        batch_size = 10
        for idx, i in enumerate(range(0, len(tokens), batch_size), start=1):
            batch = tokens[i:i + batch_size]
            response = oneapi.add_channel(name = "Cursor",
                                          base_url = oneapi_channel_url,
                                          key = '\n'.join(batch),
                                          models = Cursor.models,
                                          tags = "Cursor")
            print(f'[OneAPI] Add Channel Request For Batch {idx}. Status Code: {response.status_code}, Response Body: {response.json()}')

if __name__ == "__main__":
    main()
