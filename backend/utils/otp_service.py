import random
import smtplib
from email.mime.text import MIMEText

def generate_otp(length=6):
    """Generate a random numeric OTP."""
    return ''.join(str(random.randint(0, 9)) for _ in range(length))

def send_otp_email(to_email, otp):
    """Send OTP via email."""
    sender_email = "your_email@gmail.com"
    sender_password = "your_email_password"  # use App Password for Gmail
    subject = "Your OTP Code"
    body = f"Your OTP code is: {otp}"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        print(f"OTP sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send OTP: {e}")
