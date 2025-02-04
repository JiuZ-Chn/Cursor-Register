import copy
from DrissionPage import Chromium

class EmailServer:

    def __init__(self, browser: Chromium):
        pass

    def get_email_address(self):
        raise NotImplementedError
    
    def wait_for_message(self, delay=5, timeout=60):
        raise NotImplementedError

    def wait_for_new_message(self, delay=5, timeout=60):
        raise NotImplementedError
    
    def wait_for_new_message_thread(self, queue, delay=1, timeout=300):
        try:
            data = self.wait_for_new_message(delay=delay, timeout=timeout)
            queue.put(copy.deepcopy(data))
        except Exception as e:
            queue.put(None)
