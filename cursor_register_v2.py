import os
import re
import csv
import copy
import queue
import argparse
import threading
import concurrent.futures
from faker import Faker
from datetime import datetime
from DrissionPage import ChromiumOptions, Chromium

from temp_mails import Tempmail_io, Guerillamail_com
from helper.cursor_register import CursorRegister
from helper.email.temp_mails_wrapper import TempMailsWrapper
from helper.email.minuteinbox_com import Minuteinboxcom
from helper.email import EmailServer

# Parameters for debugging purpose
hide_account_info = os.getenv('HIDE_ACCOUNT_INFO', 'false').lower() == 'true'
enable_headless = os.getenv('ENABLE_HEADLESS', 'false').lower() == 'true'
enable_browser_log = os.getenv('ENABLE_BROWSER_LOG', 'true').lower() == 'true' or not enable_headless

def register_cursor_core(options):

    try:
        # Maybe fail to open the browser
        browser = Chromium(options)
    except Exception as e:
        print(e)
        return None

    # Opiton 1: Use temp_mails library
    #temp_email = Guerillamail_com()
    #email_server = TempMailsWrapper(temp_email)
    # Option 2: Use custom email server
    email_server = Minuteinboxcom(browser)

    # Get email address
    email = email_server.get_email_address()

    register = CursorRegister(browser, email_server)
    tab_signin, status = register.sign_in(email)
    #tab_signin, status = register.sign_up(email)

    token = register.get_cursor_cookie(tab_signin)

    if status or not enable_browser_log:
        register.browser.quit(force=True, del_data=True)

    if status and not hide_account_info:
        print(f"[Register] Cursor Email: {email}")
        print(f"[Register] Cursor Token: {token}")

    ret = {
        "username": email,
        "token": token
    }

    return ret

def register_cursor(number, max_workers):

    options = ChromiumOptions()
    options.auto_port()
    options.new_env()
    # Use turnstilePatch from https://github.com/TheFalloutOf76/CDP-bug-MouseEvent-.screenX-.screenY-patcher
    options.add_extension("turnstilePatch")

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

    # Run the code using multithreading
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(register_cursor_core, copy.deepcopy(options)) for _ in range(number)]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result is not None:
                results.append(result)

    results = [result for result in results if result["token"] is not None]

    if len(results) > 0:
        formatted_date = datetime.now().strftime("%Y-%m-%d")

        csv_file = f"./output_{formatted_date}.csv"
        token_file = f"./token_{formatted_date}.csv"

        fieldnames = results[0].keys()
        # Write username, token into a csv file
        with open(csv_file, 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writerows(results)
        # Only write token to csv file, without header
        tokens = [{'token': row['token']} for row in results]
        with open(token_file, 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['token'])
            writer.writerows(tokens)

    return results

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Cursor Registor')
    parser.add_argument('--number', type=int, default=2, help="How many account you want")
    parser.add_argument('--max_workers', type=int, default=1, help="How many workers in multithreading")
    
    # The parameters with name starts with oneapi are used to uploead the cookie token to one-api, new-api, chat-api server.
    parser.add_argument('--oneapi', action='store_true', help='Enable One-API or not')
    parser.add_argument('--oneapi_url', type=str, required=False, help='URL link for One-API website')
    parser.add_argument('--oneapi_token', type=str, required=False, help='Token for One-API website')
    parser.add_argument('--oneapi_channel_url', type=str, required=False, help='Base url for One-API channel')

    args = parser.parse_args()
    number = args.number
    max_workers = args.max_workers
    use_oneapi = args.oneapi
    oneapi_url = args.oneapi_url
    oneapi_token = args.oneapi_token
    oneapi_channel_url = args.oneapi_channel_url

    print(f"[Register] Start to register {number} accounts in {max_workers} threads")
    account_infos = register_cursor(number, max_workers)
    tokens = list(set([row['token'] for row in account_infos]))
    print(f"[Register] Register {len(tokens)} accounts successfully")
    
    if use_oneapi and len(account_infos) > 0:
        from tokenManager.oneapi_manager import OneAPIManager
        from tokenManager.cursor import Cursor
        oneapi = OneAPIManager(oneapi_url, oneapi_token)

        # Send request by batch to avoid "Too many SQL variables" error in SQLite.
        # If you use MySQL, better to set the batch_size as len(tokens)
        batch_size = 10
        for idx, i in enumerate(range(0, len(tokens), batch_size), start=1):
            batch = tokens[i:i + batch_size]
            response = oneapi.add_channel("Cursor",
                                          oneapi_channel_url,
                                          '\n'.join(batch),
                                          Cursor.models,
                                          tags = "Cursor")
            print(f'[OneAPI] Add Channel Request For Batch {idx}. Status Code: {response.status_code}, Response Body: {response.json()}')
