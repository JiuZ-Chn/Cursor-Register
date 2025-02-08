import os
import re
import queue
import threading
from faker import Faker
from DrissionPage import Chromium
from helper.email import EmailServer

enable_register_log = True

class CursorRegister:
    CURSOR_URL = "https://www.cursor.com/"
    CURSOR_SIGNIN_URL = "https://authenticator.cursor.sh"
    CURSOR_PASSWORD_URL = "https://authenticator.cursor.sh/password"
    CURSOR_MAGAIC_CODE_URL = "https://authenticator.cursor.sh/magic-code"
    CURSOR_SIGNUP_URL = "https://authenticator.cursor.sh/sign-up"
    CURSOR_SIGNUP_PASSWORD_URL = "https://authenticator.cursor.sh/sign-up/password"
    CURSOR_EMAIL_VERIFICATION_URL = "https://authenticator.cursor.sh/email-verification"

    def __init__(self, 
                 browser: Chromium,
                 email_server: EmailServer = None):

        self.browser = browser
        self.email_server = email_server
        self.email_queue = queue.Queue()
        self.email_thread = None

        self.thread_id = threading.current_thread().ident
        self.retry_times = 5

    def sign_in(self, email, password = None):

        assert any(x is not None for x in (self.email_server, password)), "Should provide email server or password. At least one of them."
 
        if self.email_server is not None:
            self.email_thread = threading.Thread(target=self.email_server.wait_for_new_message_thread,
                                                 args=(self.email_queue, ), 
                                                 daemon=True)
            self.email_thread.start()

        tab = self.browser.new_tab(self.CURSOR_SIGNIN_URL)
        # Input email
        for retry in range(self.retry_times):
            try:
                if enable_register_log: print(f"[Register][{self.thread_id}][{retry}] Input email")
                tab.ele("xpath=//input[@name='email']").input(email, clear=True)
                tab.ele("@type=submit").click()

                # If not in password page, try pass turnstile page
                if not tab.wait.url_change(self.CURSOR_PASSWORD_URL, timeout=3) and self.CURSOR_SIGNIN_URL in tab.url:
                    if enable_register_log: print(f"[Register][{self.thread_id}][{retry}] Try pass Turnstile for email page")
                    self._cursor_turnstile(tab)

            except Exception as e:
                print(f"[Register][{self.thread_id}] Exception when handlding email page.")
                print(e)

            # In password page or data is validated, continue to next page
            if tab.wait.url_change(self.CURSOR_PASSWORD_URL, timeout=5):
                print(f"[Register][{self.thread_id}] Continue to password page")
                break

            tab.refresh()
            # Kill the function since time out 
            if retry == self.retry_times - 1:
                print(f"[Register][{self.thread_id}] Timeout when inputing email address")
                return tab, False

        # Use email sign-in code in password page
        for retry in range(self.retry_times):
            try:
                if enable_register_log: print(f"[Register][{self.thread_id}][{retry}] Input password")
                if password is None:
                    tab.ele("xpath=//button[@value='magic-code']").click()

                # If not in verification code page, try pass turnstile page
                if not tab.wait.url_change(self.CURSOR_MAGAIC_CODE_URL, timeout=3) and self.CURSOR_PASSWORD_URL in tab.url:
                    if enable_register_log: print(f"[Register][{self.thread_id}][{retry}] Try pass Turnstile for password page")
                    self._cursor_turnstile(tab)

            except Exception as e:
                print(f"[Register][{self.thread_id}] Exception when handling password page.")
                print(e)

            # In code verification page or data is validated, continue to next page
            if tab.wait.url_change(self.CURSOR_MAGAIC_CODE_URL, timeout=5):
                print(f"[Register][{self.thread_id}] Continue to email code page")
                break

            if tab.wait.eles_loaded("xpath=//div[contains(text(), 'Sign up is restricted.')]", timeout=3):
                print(f"[Register][{self.thread_id}][Error] Sign up is restricted.")
                return tab, False

            tab.refresh()
            # Kill the function since time out 
            if retry == self.retry_times - 1:
                if enable_register_log: print(f"[Register][{self.thread_id}] Timeout when inputing password")
                return tab, False

        # Get email verification code
        try:
            verify_code = None

            data = self.email_queue.get(timeout=60)
            assert data is not None, "Fail to get code from email."

            if "content" in data:
                message = data["content"]
                message = message.replace(" ", "")
                verify_code = re.search(r'(?:\r?\n)(\d{6})(?:\r?\n)', message).group(1)
            assert verify_code is not None, "Fail to parse code from email."
        except Exception as e:
            print(f"[Register][{self.thread_id}] Fail to get code from email.")
            return tab, False

        # Input email verification code
        for retry in range(self.retry_times):
            try:
                if enable_register_log: print(f"[Register][{self.thread_id}][{retry}] Input email verification code")

                for idx, digit in enumerate(verify_code, start = 0):
                    tab.ele(f"xpath=//input[@data-index={idx}]").input(digit, clear=True)
                    tab.wait(0.1, 0.3)
                tab.wait(0.5, 1.5)

                if not tab.wait.url_change(self.CURSOR_URL, timeout=3) and self.CURSOR_MAGAIC_CODE_URL in tab.url:
                    if enable_register_log: print(f"[Register][{self.thread_id}][{retry}] Try pass Turnstile for email code page.")
                    self._cursor_turnstile(tab)

            except Exception as e:
                print(f"[Register][{self.thread_id}] Exception when handling email code page.")
                print(e)

            if tab.wait.url_change(self.CURSOR_URL, timeout=3):
                break

            tab.refresh()
            # Kill the function since time out 
            if retry == self.retry_times - 1:
                if enable_register_log: print(f"[Register][{self.thread_id}] Timeout when inputing email verification code")
                return tab, False

        return tab, True

    def sign_up(self, email, password = None):

        assert self.email_server is not None, "Should provide email server."
 
        if self.email_server is not None:
            self.email_thread = threading.Thread(target=self.email_server.wait_for_new_message_thread,
                                                 args=(self.email_queue, ), 
                                                 daemon=True)
            self.email_thread.start()

        if password is None:
            fake = Faker()
            password = fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)

        tab = self.browser.new_tab(self.CURSOR_SIGNUP_URL)
        # Input email
        for retry in range(self.retry_times):
            try:
                if enable_register_log: print(f"[Register][{self.thread_id}][{retry}] Input email")
                tab.ele("xpath=//input[@name='email']").input(email, clear=True)
                tab.ele("@type=submit").click()

                # If not in password page, try pass turnstile page
                if not tab.wait.url_change(self.CURSOR_SIGNUP_PASSWORD_URL, timeout=3) and self.CURSOR_SIGNUP_URL in tab.url:
                    if enable_register_log: print(f"[Register][{self.thread_id}][{retry}] Try pass Turnstile for email page")
                    self._cursor_turnstile(tab)

            except Exception as e:
                print(f"[Register][{self.thread_id}] Exception when handlding email page.")
                print(e)

            # In password page or data is validated, continue to next page
            if tab.wait.url_change(self.CURSOR_SIGNUP_PASSWORD_URL, timeout=5):
                print(f"[Register][{self.thread_id}] Continue to password page")
                break

            tab.refresh()
            # Kill the function since time out 
            if retry == self.retry_times - 1:
                print(f"[Register][{self.thread_id}] Timeout when inputing email address")
                return tab, False

        # Use email sign-in code in password page
        for retry in range(self.retry_times):
            try:
                if enable_register_log: print(f"[Register][{self.thread_id}][{retry}] Input password")
                tab.ele("xpath=//input[@name='password']").input(password, clear=True)
                tab.ele('@type=submit').click()

                # If not in verification code page, try pass turnstile page
                if not tab.wait.url_change(self.CURSOR_EMAIL_VERIFICATION_URL, timeout=3) and self.CURSOR_SIGNUP_PASSWORD_URL in tab.url:
                    if enable_register_log: print(f"[Register][{self.thread_id}][{retry}] Try pass Turnstile for password page")
                    self._cursor_turnstile(tab)

            except Exception as e:
                print(f"[Register][{self.thread_id}] Exception when handling password page.")
                print(e)

            # In code verification page or data is validated, continue to next page
            if tab.wait.url_change(self.CURSOR_EMAIL_VERIFICATION_URL, timeout=5):
                print(f"[Register][{self.thread_id}] Continue to email code page")
                break

            if tab.wait.eles_loaded("xpath=//div[contains(text(), 'Sign up is restricted.')]", timeout=3):
                print(f"[Register][{self.thread_id}][Error] Sign up is restricted.")
                return tab, False

            tab.refresh()
            # Kill the function since time out 
            if retry == self.retry_times - 1:
                if enable_register_log: print(f"[Register][{self.thread_id}] Timeout when inputing password")
                return tab, False

        # Get email verification code
        try:
            data = self.email_queue.get(timeout=60)
            assert data is not None, "Fail to get code from email."

            verify_code = None
            if "body_text" in data:
                message_text = data["body_text"]
                message_text = message_text.replace(" ", "")
                verify_code = re.search(r'(?:\r?\n)(\d{6})(?:\r?\n)', message_text).group(1)
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
            print(f"[Register][{self.thread_id}] Fail to get code from email.")
            return tab, False

        # Input email verification code
        for retry in range(self.retry_times):
            try:
                if enable_register_log: print(f"[Register][{self.thread_id}][{retry}] Input email verification code")

                for idx, digit in enumerate(verify_code, start = 0):
                    tab.ele(f"xpath=//input[@data-index={idx}]").input(digit, clear=True)
                    tab.wait(0.1, 0.3)
                tab.wait(0.5, 1.5)

                if not tab.wait.url_change(self.CURSOR_URL, timeout=3) and self.CURSOR_EMAIL_VERIFICATION_URL in tab.url:
                    if enable_register_log: print(f"[Register][{self.thread_id}][{retry}] Try pass Turnstile for email code page.")
                    self._cursor_turnstile(tab)

            except Exception as e:
                print(f"[Register][{self.thread_id}] Exception when handling email code page.")
                print(e)

            if tab.wait.url_change(self.CURSOR_URL, timeout=3):
                break

            tab.refresh()
            # Kill the function since time out 
            if retry == self.retry_times - 1:
                if enable_register_log: print(f"[Register][{self.thread_id}] Timeout when inputing email verification code")
                return tab, False

        return tab, True

    # tab: A tab has signed in 
    def delete_account(self, tab):
        pass

    def get_cursor_cookie(self, tab):
        try:
            cookies = tab.cookies().as_dict()
        except:
            print(f"[Register][{self.thread_id}] Fail to get cookie.")
            return None

        token = cookies.get('WorkosCursorSessionToken', None)
        if enable_register_log:
            if token is not None:
                print(f"[Register][{self.thread_id}] Register Account Successfully.")
            else:
                print(f"[Register][{self.thread_id}] Register Account Failed.")

        return token

    def _cursor_turnstile(self, tab, retry_times = 5):
        for retry in range(retry_times): # Retry times
            try:
                if enable_register_log: print(f"[Register][{self.thread_id}][{retry}] Passing Turnstile")
                challenge_shadow_root = tab.ele('@id=cf-turnstile').child().shadow_root
                challenge_shadow_button = challenge_shadow_root.ele("tag:iframe", timeout=30).ele("tag:body").sr("xpath=//input[@type='checkbox']")
                if challenge_shadow_button:
                    challenge_shadow_button.click()
                    break
            except:
                pass
            if retry == retry_times - 1:
                print("[Register] Timeout when passing turnstile")
