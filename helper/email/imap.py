import time
import imaplib
import email

from _email_server import EmailServer

class Imap(EmailServer):

    def __init__(self, imap_server, username, password):
        self.mail = imaplib.IMAP4_SSL(imap_server)
        self.mail.login(username, password)
        self.mail.select('inbox')
        
    def wait_for_message(self, delay=5, timeout=60):

        # Search for all emails and get their IDs
        result, data = self.mail.search(None, 'ALL')
        email_ids = data[0].split()
        if not email_ids:
            raise Exception("No emails found.")

        # Pick the most recent email (last in the list)
        latest_id = email_ids[-1]

        # Fetch the email message by ID
        result, data = self.mail.fetch(latest_id, '(RFC822)')
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Extract common headers
        from_header = msg.get('From')
        to_header = msg.get('To')

        # Extract email content (plain text)
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                # Look for the plain text part and avoid attachments
                if part.get_content_type() == "text/plain" and not part.get('Content-Disposition'):
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8'
                    body = payload.decode(charset, errors='replace')
                    break
        else:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or 'utf-8'
            body = payload.decode(charset, errors='replace')


        return {
            "from": from_header,
            "to": to_header,
            "text": body
        }

    def __del__(self):
        self.mail.logout()



