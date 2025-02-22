import time
import imaplib
import email
from email.policy import default
from datetime import datetime

from ._email_server import EmailServer

class Imap(EmailServer):

    def __init__(self, imap_server, imap_port, username, password, email_to = None):
        self.mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        self.mail.login(username, password)

        self.email_to = email_to
        
        self.mail.select('inbox')
        _, data = self.mail.uid("SEARCH", None, 'ALL')
        email_ids = data[0].split()
        self.latest_id = email_ids[-1] if len(email_ids) != 0 else None

    def fetch_emails_since(self, since_timestamp):

        # Get the latest email by id
        self.mail.select('inbox')
        search_criteria = f'UID {int(self.latest_id) + 1}:*' if self.latest_id else 'ALL'
        _, data = self.mail.uid("SEARCH", None, search_criteria)
        email_ids = data[0].split()
        if len(email_ids) == 0:
            return None
        self.latest_id = email_ids[-1]
        
        # Fetch the email message by ID
        _, data = self.mail.uid('FETCH', self.latest_id, '(RFC822)')
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email, policy=default)

        # Extract common headers
        from_header = msg.get('From')
        to_header = msg.get('To')
        subject_header = msg.get('Subject')
        date_header = msg.get('Date')

        if self.email_to not in (None, to_header):
            return None

        email_datetime = datetime.strptime(date_header.replace(' (UTC)', ''), '%a, %d %b %Y %H:%M:%S %z').timestamp()
        if email_datetime < since_timestamp:
            return None

        text_part = msg.get_body(preferencelist=('plain',))
        content = text_part.get_content() if text_part else msg.get_content()

        return {
            "from": from_header,
            "to": to_header,
            "date": date_header,
            "subject": subject_header,
            "content": content
        }
    
    def wait_for_new_message(self, delay=5, timeout=60):
        start_time = time.time()

        while time.time() - start_time <= timeout:
            try:
                email = self.fetch_emails_since(start_time)
                if email is not None:
                    return email
            except:
                pass
            time.sleep(delay)

        return None
