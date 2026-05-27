from app.models.member import Member
from app.models.notification import Notification

class NotificationService:
    def send_notification(self, member: Member, notification: Notification) -> None:
        member.update(notification)
