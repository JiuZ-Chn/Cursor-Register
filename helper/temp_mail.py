import random
import inspect

import temp_mails

class TempMail:

    disallowed_list = {
        "Internxt_com": "Hard Ratelimit",
        "Minutemailbox_com": "Server broken",
        "Temils_com": "Offline",
        "Tempmail_gg": "Offline",
        "Yopmail_com": "Captcha",
        "Fakermail_com": "Offline",
        "Mailcatch_com": "Offline",
        "Rainmail_xyz": "Offline",
        "Crazymailing_com": "Offline",
        "Adguard_com": "Captcha",
        "Tempmailbeast_com": "No service anymore",
        "Tempmailers_com": "Offline",
        "Schutzmail_de": "Offline",
        "Maildax_com": "Captcha",
        "Getnada_cc": "Broken",
        "Wptempmail_com": "Offline",

        "Mail_tm": "Not allowed by Cursor"
    }

    def __init__(self):
        pass

    @classmethod
    def get_random_mail_class(cls, allow_mail_class_strs = []):
    
        mail_class_strs = temp_mails.__all_providers__
        mail_class_strs = [mail_class_str for mail_class_str in mail_class_strs if mail_class_str not in cls.disallowed_list]
        if len(allow_mail_class_strs) > 0:
            mail_class_strs = [mail_class_str for mail_class_str in mail_class_strs if mail_class_str in allow_mail_class_strs]
        random.shuffle(mail_class_strs)

        whitelisted_args = ("self", "name", "domain", "exclude", "password")
        for mail_class_str in mail_class_strs:
            mail_class = temp_mails.__getattribute__(mail_class_str)
            args = inspect.getfullargspec(mail_class).args
            if set(args).issubset(set(whitelisted_args)):
                try:
                    mail_class()
                    print(f"[TempMail] Use temp mail server from {mail_class_str}")
                    return mail_class
                except:
                    print(f"[TempMail] Fail to init temp email class for {mail_class_str}")

        return None