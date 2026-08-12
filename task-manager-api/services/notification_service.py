import smtplib
import logging
import os
from datetime import datetime

class NotificationService:
    def __init__(self, email_host=None, email_port=None, email_user=None, email_password=None):
        self.notifications = []
        self.email_host = email_host or os.getenv('SMTP_HOST')
        self.email_port = int(email_port or os.getenv('SMTP_PORT', '587'))
        self.email_user = email_user or os.getenv('SMTP_USER')
        self.email_password = email_password or os.getenv('SMTP_PASSWORD')

    def send_email(self, to, subject, body):
        if not all((self.email_host, self.email_user, self.email_password)):
            logging.getLogger(__name__).error("SMTP configuration is incomplete")
            return False
        try:
            server = smtplib.SMTP(self.email_host, self.email_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(self.email_user, to, message)
            server.quit()
            logging.getLogger(__name__).info("Email sent", extra={"recipient": to})
            return True
        except (smtplib.SMTPException, OSError):
            logging.getLogger(__name__).exception("Email delivery failed")
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\nPrioridade: {task.priority}\nStatus: {task.status}"
        self.send_email(user.email, subject, body)
        self.notifications.append({
            'type': 'task_assigned',
            'user_id': user.id,
            'task_id': task.id,
            'timestamp': datetime.utcnow()
        })

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        result = []
        for n in self.notifications:
            if n['user_id'] == user_id:
                result.append(n)
        return result
