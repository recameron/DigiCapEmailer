import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import logging

load_dotenv()  # For local testing; in GCP set env vars instead

# MongoDB setup
MONGO_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGO_URI)
db = client.get_database()
entries = db.entries

# Gmail SMTP setup
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

def send_email_gmail(to_email, subject, body_text):
    msg = MIMEText(body_text)
    msg['Subject'] = subject
    msg['From'] = GMAIL_USER
    msg['To'] = to_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, [to_email], msg.as_string())
    print(f"Email sent to {to_email}")

def send_time_capsules(request):
    try:
        now = datetime.utcnow()

        # Find all entries where sent == False and unlock_datetime <= now
        unsent_capsules = entries.find({
            "sent": False,
            "unlock_datetime": {"$lte": now}
        })

        count = 0
        for capsule in unsent_capsules:
            try:
                to_email = capsule["recipientEmail"]
                message = capsule["message"]

                send_email_gmail(to_email, "Your Digital Time Capsule", message)

                # Mark as sent
                entries.update_one({"_id": capsule["_id"]}, {"$set": {"sent": True}})
                count += 1
            except Exception as e:
                print(f"Error sending email for entry {capsule['_id']}: {e}")
        return f"Processed {count} capsules", 200
    except Exception as e:
        logging.exception("Unhandled error in send_time_capsules")
        return f"Internal server error: {e}", 500
