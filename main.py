import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from google.cloud import storage, firestore
from datetime import datetime
from dotenv import load_dotenv
import logging

load_dotenv()  # For local testing; in GCP set env vars instead


db = firestore.Client()
entries = db.collection("entries")

# Gmail SMTP setup
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

def send_email_gmail(to_email, subject, body_text, attachment_bytes=None, attachment_filename=None):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = GMAIL_USER
    msg['To'] = to_email

    msg.attach(MIMEText(body_text, 'plain'))

    if attachment_bytes and attachment_filename:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment_bytes)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{attachment_filename}"')
        msg.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, [to_email], msg.as_string())
    print(f"Email sent to {to_email}")


def send_time_capsules(request=None):
    try:
        now = datetime.utcnow()

        # Query unsent + unlockable capsules
        unsent_capsules = entries.where("sent", "==", False).where("unlock_datetime", "<=", now).stream()

        storage_client = storage.Client()
        bucket_name = os.environ.get("GCS_BUCKET_NAME")
        bucket = storage_client.bucket(bucket_name)

        count = 0
        for doc in unsent_capsules:
            capsule = doc.to_dict()
            doc_id = doc.id

            try:
                to_email = capsule["recipientEmail"]
                message = capsule["message"]
                attachment_bytes = None
                attachment_filename = None

                blob_name = capsule.get("imageBlobName")
                if blob_name:
                    blob = bucket.blob(blob_name)
                    attachment_bytes = blob.download_as_bytes()
                    attachment_filename = os.path.basename(blob_name)

                send_email_gmail(
                    to_email,
                    "Your Digital Time Capsule",
                    message,
                    attachment_bytes=attachment_bytes,
                    attachment_filename=attachment_filename
                )

                # Mark as sent
                entries.document(doc_id).update({"sent": True})
                count += 1

            except Exception as e:
                print(f"Error sending email for entry {doc_id}: {e}")

        return f"Processed {count} capsules", 200

    except Exception as e:
        logging.exception("Unhandled error in send_time_capsules")
        return f"Internal server error: {e}", 500

