from temp_mails._constructors import _WaitForMail

from ._email_server import EmailServer

class TempMailsWrapper(EmailServer):

    def __init__(self, provider: _WaitForMail):
        self.provider = provider

    def get_email_address(self):
        return self.provider.email
    
    def wait_for_new_message(self, delay=5, timeout=60):
        return self.provider.wait_for_new_email(delay=delay, timeout=timeout)

if __name__ == "__main__":
    pass
    
