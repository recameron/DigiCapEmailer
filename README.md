# Digital Time Capsule Emailer

This is a Google Cloud Function that retrieves scheduled "digital time capsule" messages from a Google Firestore collection and emails them to recipients when their unlock date has arrived. This is meant to add emailing functionality to DigiCap (https://github.com/recameron/DigiCap).

## Features

- Automatically checks for unsent messages with unlock dates in the past
- Sends the messages via Gmail's SMTP server
- Marks messages as "sent" in Firestore to avoid duplication
- Deployable via `gcloud` CLI

## Notes
- Messages are only sent when `unlock_datetime` is in the past and `sent` is false.
- Check logs in the Google Cloud Console if anything goes wrong.
- Don't commit your passwords or secret files to GitHub.

