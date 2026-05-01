from typing import Dict, List, Callable, Set
import email_sender
import template_manager


class EmailSenderAdapter:
    def __init__(self, progress_callback: Callable):
        self.progress_callback = progress_callback
        self.service = None
        self.sent_log: Set[str] = set()

    def authenticate(self) -> bool:
        try:
            self.service = email_sender.authenticate()
            return True
        except Exception:
            return False

    def load_sent_log(self) -> None:
        self.sent_log = email_sender.load_sent_log()

    def send_campaign(self, leads: List[Dict], config: Dict, stop_flag_check: Callable) -> None:
        daily_limit = config.get("daily_limit", 50)
        delay_seconds = config.get("delay_seconds", 30)
        template_id = config.get("template_id")
        sent_count = 0

        # Get template
        if template_id:
            template = template_manager.get_template_by_id(template_id)
        else:
            template = template_manager.get_default_template()
        
        if not template:
            raise Exception("No email template found")

        # Sender info for template
        sender_info = {
            "name": email_sender.SENDER_NAME,
            "phone": email_sender.SENDER_PHONE,
            "portfolio": email_sender.SENDER_PORTFOLIO,
        }

        for lead in leads:
            if stop_flag_check():
                break

            email = lead.get("email", "")

            if email_sender.is_duplicate(email, self.sent_log):
                self.progress_callback("skipped", lead)
                continue

            # Use template to generate email
            subject, body = template_manager.format_email(template, lead, sender_info)

            self.progress_callback("processing", lead)

            try:
                success = email_sender.send_email(self.service, email, subject, body)
                if success:
                    email_sender.mark_as_sent(email, self.sent_log)
                    sent_count += 1
                    self.progress_callback("sent", lead)
                    if sent_count >= daily_limit:
                        break
                    email_sender.apply_delay(delay_seconds)
                else:
                    self.progress_callback("failed", lead)
            except Exception as e:
                self.progress_callback("failed", lead, str(e))
