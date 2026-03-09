#!/usr/bin/env python3
"""
Simple health check script for Receipt Helper.
Pings the backend health endpoint and sends an email notification via SMTP.
Designed to be run by cron 4 times a day (e.g., `0 */6 * * *`).

Setup:
1. Copy this file to your VPS: `health_check.py`
2. Make it executable: `chmod +x health_check.py`
3. Edit the settings below (SMTP server, email, password, TARGET_URL).
4. Run `crontab -e` and add: `0 */6 * * * /usr/bin/python3 /path/to/health_check.py`
"""

import urllib.request
import smtplib
from email.message import EmailMessage
from datetime import datetime

# ================= Configuration =================
TARGET_URL = "http://localhost:8080/api/health"  # Adjust if the port is different or use public IP/domain
SMTP_SERVER = "smtp.gmail.com"                   # e.g., smtp.gmail.com, smtp.qq.com
SMTP_PORT = 465                                  # Usually 465 for SSL or 587 for TLS
SMTP_USERNAME = "your_email@gmail.com"           # Your sending email address
SMTP_PASSWORD = "your_app_password"              # App password (not regular password)
RECIPIENT_EMAIL = "your_email@gmail.com"         # Where to send the report
# ===============================================

def send_email(subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USERNAME
    msg["To"] = RECIPIENT_EMAIL

    try:
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
        print("Email notification sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = f"[Receipt Helper] Health Check Report - {now}"
    
    try:
        req = urllib.request.Request(TARGET_URL)
        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.getcode()
            body = response.read().decode('utf-8')
            
            if status_code == 200:
                print(f"[{now}] Health check OK. Status: {status_code}")
                email_body = (
                    f"Receipt Helper Backend is ONLINE.\n\n"
                    f"Timestamp: {now}\n"
                    f"URL Checked: {TARGET_URL}\n"
                    f"Status Code: {status_code}\n"
                    f"Response: {body}"
                )
            else:
                print(f"[{now}] Health check WARNING. Status: {status_code}")
                subject = f"[ALERT] {subject}"
                email_body = (
                    f"Receipt Helper Backend returned an unexpected status code.\n\n"
                    f"Timestamp: {now}\n"
                    f"URL Checked: {TARGET_URL}\n"
                    f"Status Code: {status_code}\n"
                    f"Response: {body}"
                )
    except Exception as e:
        print(f"[{now}] Health check FAILED: {e}")
        subject = f"[DOWN] {subject}"
        email_body = (
            f"Receipt Helper Backend appears to be DOWN.\n\n"
            f"Timestamp: {now}\n"
            f"URL Checked: {TARGET_URL}\n"
            f"Error: {e}\n\n"
            f"Please check your VPS and Docker containers."
        )

    send_email(subject, email_body)

if __name__ == "__main__":
    main()
