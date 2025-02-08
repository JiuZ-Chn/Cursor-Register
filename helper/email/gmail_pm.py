import time
from DrissionPage import Chromium

from ._email_server import EmailServer

class Gmailpm(EmailServer):
    GMAIL_PM_URL = "https://gmail.pm/"

    def __init__(self, browser: Chromium):
        self.tab = browser.new_tab(self.GMAIL_PM_URL)

    def get_email_address(self):
        email_address = None

        for _ in range(5):
            self.tab.wait(5)
            shortid = self.tab.ele("xpath=//input[@id='shortid']", timeout=5).value
            if shortid != "":
                email_address = shortid
                break

        if email_address is None:
            print("[gmail.pm] Fail to get email address from gmail.pm.")
            return None
        
        return email_address
        
    def wait_for_new_message(self, delay=5, timeout=60):
        start_time = time.time()

        while time.time() - start_time <= timeout:
            try:
                maillist = self.tab.ele("xpath=//tbody[@id='maillist']")
                maillist_trs = maillist.children()
                if len(maillist_trs) > 0:
                    maillist_trs[0].children()[0].click()
                    content = self.tab.ele("xpath=//div[@class='content'][title]")

                    return {
                        "content": content.text
                    }
            except:
                pass
            
            self.tab.wait(delay)
        return None
