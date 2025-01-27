import time

from DrissionPage import Chromium

class Gmailpm:

    GMAIL_PM_URL = "https://gmail.pm/"

    def __init__(self, browser: Chromium):
        self.tab = browser.new_tab(self.GMAIL_PM_URL)
        self.tab._wait_loaded()

    def get_email_address(self, custom_address = None):
        email_address = None
        if custom_address is not None:
            self.tab.wait(3, 5)
            custom_shortid = self.tab.ele("xpath=//i[@id='customShortid']")
            custom_shortid.click()
            self.tab.ele("xpath=//input[@id='shortid']").input(custom_address, clear =True)
            custom_shortid.click()
            self.tab.wait(3, 5)

        for _ in range(5):
            self.tab.wait(5)
            shortid = self.tab.ele("xpath=//input[@id='shortid']").value
            if shortid != "":
                email_address = shortid
                break

        if email_address is None:
            print("[gmail.pm] Fail to get email address from gmail.pm.")
            return None
        
        return email_address
        
    def wait_for_message(self, delay=5, timeout=60):

        start_time = time.time()

        while time.time() - start_time <= timeout:

            try:
                maillist = self.tab.ele("xpath=//tbody[@id='maillist']")
                maillist_trs = maillist.children()
                if len(maillist_trs) > 0:
                    maillist_trs[0].children()[0].click()
                    self.tab.wait(1, 1.5)
                    content = self.tab.ele("xpath=//div[@class='content'][title]")

                    return {
                        "text": content.text
                    }

                self.tab.wait(delay)

            except:
                pass

        return None





