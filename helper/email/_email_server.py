import time

from DrissionPage import Chromium

class EmailServer:

    def __init__(self, browser: Chromium):
        pass

    def get_email_address(self):
        raise NotImplementedError
        
    def wait_for_message(self, delay=5, timeout=60):
        raise NotImplementedError
