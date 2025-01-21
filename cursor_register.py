import os
import re
import csv
import copy
import queue
import argparse
import threading
import concurrent.futures
from sys import platform
from datetime import datetime

from faker import Faker
from DrissionPage import ChromiumOptions, Chromium
from temp_mails import Tempmail_lol, Guerillamail_com

CURSOR_URL = "https://www.cursor.com/"
CURSOR_LOGIN_URL = "https://authenticator.cursor.sh"
CURSOR_SIGN_UP_URL =  "https://authenticator.cursor.sh/sign-up"
CURSOR_SETTINGS_URL = "https://www.cursor.com/settings"

# Parameters for debugging purpose
hide_account_info = os.getenv('HIDE_ACCOUNT_INFO', 'false').lower() == 'true'
enable_register_log = True
enable_headless = os.getenv('ENABLE_HEADLESS', 'false').lower() == 'true'
enable_browser_log = os.getenv('ENABLE_BROWSER_LOG', 'true').lower() == 'true' or not enable_headless

def cursor_turnstile(tab, retry_times = 5):
    thread_id = threading.current_thread().ident

    for retry in range(retry_times): # Retry times
        try:
            if enable_register_log: print(f"[Register][{thread_id}][{retry}] Passing Turnstile")
            challenge_shadow_root = tab.ele('@id=cf-turnstile').child().shadow_root
            challenge_shadow_button = challenge_shadow_root.ele("tag:iframe", timeout=30).ele("tag:body").sr("xpath=//input[@type='checkbox']")
            if challenge_shadow_button:
                challenge_shadow_button.click()
                tab.wait.load_start()
                break
        except:
            pass
        if retry == retry_times - 1:
            print("[Register] Timeout when passing turnstile")

def sign_up(options):

    def wait_for_new_email_thread(mail, queue, timeout=300):
        try:
            data = mail.wait_for_new_email(delay=1, timeout=timeout)
            queue.put(copy.deepcopy(data))
        except Exception as e:
            queue.put(None)

    # Maybe fail to open the browser
    try:
        browser = Chromium(options)
    except Exception as e:
        print(e)
        return None

    retry_times = 5
    thread_id = threading.current_thread().ident
    
    # Get temp email address
    mail = Tempmail_lol()
    #mail = Guerillamail_com()
    email = mail.email

    # Get password and name by faker
    fake = Faker()
    password = fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
    first_name, last_name = fake.name().split(' ')[0:2]

    email_queue = queue.Queue()
    email_thread = threading.Thread(target=wait_for_new_email_thread, args=(mail, email_queue, ))
    email_thread.daemon = True
    email_thread.start()

    tab = browser.new_tab(CURSOR_SIGN_UP_URL)
    # Input first name, last name, email
    for retry in range(retry_times):
        try:
            if enable_register_log: print(f"[Register][{thread_id}][{retry}] Input first name, last name, email")
            tab.refresh()
            tab.ele("xpath=//input[@name='first_name']").input(first_name, clear=True)
            tab.ele("xpath=//input[@name='last_name']").input(last_name, clear=True)
            tab.ele("xpath=//input[@name='email']").input(email, clear=True)
            tab.ele("@type=submit").click()
            tab.wait.load_start()

            #if tab.ele("xpath=//input[@name='email']").attr("data-invalid") == "true":
            #    print(f"[Register][{thread_id}] Email is invalid")
            #    return None
            
            # In password page or data is validated, continue to next page
            if tab.wait.eles_loaded("xpath=//input[@name='password']", timeout=5):
                print(f"[Register][{thread_id}] Continue to password page")
                break
            # If not in password page, try pass turnstile page
            elif tab.ele("xpath=//input[@name='email']", timeout=3).attr("data-valid") is not None:
                if enable_register_log: print(f"[Register][{thread_id}][{retry}] Try pass Turnstile for email page")
                cursor_turnstile(tab)

        except Exception as e:
            print(f"[Register][{thread_id}] Exception when handlding email page.")
            print(e)
        
        # In password page or data is validated, continue to next page
        if tab.wait.eles_loaded("xpath=//input[@name='password']"):
            print(f"[Register][{thread_id}] Continue to password page")
            break

        # Kill the function since time out 
        if retry == retry_times - 1:
            print(f"[Register][{thread_id}] Timeout when inputing email address")
            if not enable_browser_log: browser.quit(force=True, del_data=True)
            return None
    
    # Input password
    for retry in range(retry_times):
        try:
            if enable_register_log: print(f"[Register][{thread_id}][{retry}] Input password")
            tab.ele("xpath=//input[@name='password']").input(password, clear=True)
            tab.ele('@type=submit').click()
            tab.wait.load_start()

            # In code verification page or data is validated, continue to next page
            if tab.wait.eles_loaded("xpath=//input[@data-index=0]", timeout=5):
                print(f"[Register][{thread_id}] Continue to email code page")
                break
            # If not in verification code page, try pass turnstile page
            elif tab.ele("xpath=//input[@name='password']", timeout=3).attr("data-valid") is not None:
                if enable_register_log: print(f"[Register][{thread_id}][{retry}] Try pass Turnstile for password page")
                cursor_turnstile(tab)

        except Exception as e:
            print(f"[Register][{thread_id}] Exception when handling password page.")
            print(e)

        # In code verification page or data is validated, continue to next page
        if tab.wait.eles_loaded("xpath=//input[@data-index=0]"):
            print(f"[Register][{thread_id}] Continue to email code page")
            break

        # Kill the function since time out 
        if retry == retry_times - 1:
            if enable_register_log: print(f"[Register][{thread_id}] Timeout when inputing password")
            if not enable_browser_log: browser.quit(force=True, del_data=True)
            return None

    # Get email verification code
    try:
        data = email_queue.get(timeout=60)
        assert data is not None, "Fail to get code from email."

        verify_code = None
        if "body_text" in data:
            message_text = data["body_text"]
            message_text = message_text.strip().replace('\n', '').replace('\r', '').replace('=', '')
            verify_code = re.search(r'open browser window\.(\d{6})This code expires', message_text).group(1)
        elif "preview" in data:
            message_text = data["preview"]
            verify_code = re.search(r'Your verification code is (\d{6})\. This code expires', message_text).group(1)
        # Handle HTML format
        elif "content" in data:
            message_text = data["content"]
            message_text = re.sub(r"<[^>]*>", "", message_text)
            message_text = re.sub(r"&#8202;", "", message_text)
            message_text = re.sub(r"&nbsp;", "", message_text)
            message_text = re.sub(r'[\n\r\s]', "", message_text)
            verify_code = re.search(r'openbrowserwindow\.(\d{6})Thiscodeexpires', message_text).group(1)
        assert verify_code is not None, "Fail to get code from email."

    except Exception as e:
        print(f"[Register][{thread_id}] Fail to get code from email.")
        if not enable_browser_log: browser.quit(force=True, del_data=True)
        return None

    # Input email verification code
    for retry in range(retry_times):
        try:
            if enable_register_log: print(f"[Register][{thread_id}][{retry}] Input email verification code")

            for idx, digit in enumerate(verify_code, start = 0):
                tab.ele(f"xpath=//input[@data-index={idx}]").input(digit, clear=True)
                tab.wait(0.1, 0.3)
            tab.wait(0.5, 1.5)
        except Exception as e:
            print(f"[Register][{thread_id}] Exception when handling email code page.")
            print(e)

        if tab.url != CURSOR_URL:
            if enable_register_log: print(f"[Register][{thread_id}][{retry}] Try pass Turnstile for email code page.")
            cursor_turnstile(tab)

        if tab.wait.url_change(CURSOR_URL, timeout=15):
            break

        # Kill the function since time out 
        if retry == retry_times - 1:
            if enable_register_log: print(f"[Register][{thread_id}] Timeout when inputing email verification code")
            if not enable_browser_log: browser.quit(force=True, del_data=True)
            return None

    # Get cookie
    try:
        cookies = tab.cookies().as_dict()
    except e:
        print(f"[Register][{thread_id}] Fail to get cookie.")
        if not enable_browser_log: browser.quit(force=True, del_data=True)
        return None

    token = cookies.get('WorkosCursorSessionToken', None)
    if enable_register_log:
        if token is not None:
            print(f"[Register][{thread_id}] Register Account Successfully.")
        else:
            print(f"[Register][{thread_id}] Register Account Failed.")

    if not hide_account_info:
        print(f"[Register] Cursor Email: {email}")
        print(f"[Register] Cursor Password: {password}")
        print(f"[Register] Cursor Token: {token}")

    browser.quit(force=True, del_data=True)

    return {
        'username': email,
        'password': password,
        'token': token
    }

def register_cursor(number, max_workers):

    options = ChromiumOptions()
    options.auto_port()
    # Use turnstilePatch from https://github.com/TheFalloutOf76/CDP-bug-MouseEvent-.screenX-.screenY-patcher
    options.add_extension("turnstilePatch")

    if platform == "linux" or platform == "linux2":
        platformIdentifier = "X11; Linux x86_64"
    elif platform == "darwin":
        platformIdentifier = "Macintosh; Intel Mac OS X 10_15_7"
    elif platform == "win32":
        platformIdentifier = "Windows NT 10.0; Win64; x64"
    options.set_user_agent(f"Mozilla/5.0 ({platformIdentifier}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
    if enable_headless: 
        options.headless()

    # Run the code using multithreading
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(sign_up, copy.deepcopy(options)) for _ in range(number)]
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

        # Write username, password, token into a csv file
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
                                          Cursor.models)
            print(f'[OneAPI] Add Channel Request For Batch {idx}. Status Code: {response.status_code}, Response Body: {response.json()}')
