from celery import shared_task
from django.contrib.auth import get_user_model
import time

User = get_user_model()

@shared_task
def send_welcome_email(user_id):
    user = User.objects.get(id=user_id)
    print(f"Sending welcome email to {user.email}...")
    time.sleep(5)  # Simulate email sending delay
    print("Email sent successfully!")
