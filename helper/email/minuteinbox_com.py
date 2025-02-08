import time
from DrissionPage import Chromium

from ._email_server import EmailServer

class Minuteinboxcom(EmailServer):
    MINUTEINBOX_COM_URL = "https://www.minuteinbox.com/"

    def __init__(self, browser: Chromium):
        self.tab = browser.new_tab(self.MINUTEINBOX_COM_URL)

    def get_email_address(self):
        email_address = None

        for _ in range(5):
            try:
                self.tab.wait(2)
                email = self.tab.ele("xpath=//span[@id='email']", timeout=5).text
                if email != "":
                    email_address = email
                    break
            except Exception as e:
                print(e)
                pass

        if email_address is None:
            print("[minuteinbox.com] Fail to get email address")
            return None
        
        return email_address
        
    def wait_for_new_message(self, delay=5, timeout=60):
        start_time = time.time()

        while time.time() - start_time <= timeout:
            try:
                self.tab.refresh()
                self.tab.ele("xpath=//span[contains(text(), 'Cursor')]").click()
                layout = self.tab.ele("xpath=//div[@class='base-layout-root']")

                return {
                    "text": layout.text
                }
            except:
                pass
            
            self.tab.wait(delay)
        return None

if __name__ == "__main__":
    browser = Chromium()
    email_server = Minuteinboxcom(browser)
    email = email_server.get_email_address()
    print(email)
    
