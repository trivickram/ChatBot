import smtplib
from email.message import EmailMessage
import ssl

sender = 'test-sender@example.com'
receiver = 'test-recipient@example.com'
subject = 'Test email from local SMTP'
body = 'This is a test email sent to local debug SMTP server.'

msg = EmailMessage()
msg['From'] = sender
msg['To'] = receiver
msg['Subject'] = subject
msg.set_content(body)

print('Attempting to send test email to localhost:1025 (debugging SMTP)')
try:
    with smtplib.SMTP('localhost', 1025) as server:
        server.send_message(msg)
    print('Send completed without exception.')
except Exception as e:
    print('Error:', e)
