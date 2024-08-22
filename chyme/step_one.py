import email
import imaplib
import os
import re
from email.header import decode_header
from typing import Any

from bs4 import BeautifulSoup


def connect_to_email(username, password) -> imaplib.IMAP4_SSL:
    # Connect to the email server
    mail = imaplib.IMAP4_SSL("imap.fastmail.com")
    mail.login(username, password)
    return mail


def fetch_emails(mail, receiving_email, limit_emails=False) -> list[Any]:
    # Select the mailbox (inbox)
    mail.select("inbox")

    # Search for all emails
    _status, messages = mail.search(None, "TO", receiving_email)
    email_ids = messages[0].split()

    if limit_emails:
        email_ids = email_ids[-10:]

    # Fetch all emails for testing purposes
    emails = []
    for e_id in email_ids:
        status, msg_data = mail.fetch(e_id, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        emails.append(msg)
    return emails


def get_body(msg) -> str | None:
    text = None
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain" and "attachment" not in str(
                part.get("Content-Disposition")
            ):
                text = part.get_payload(decode=True).decode()
                break  # Prioritize plain text
            elif content_type == "text/html" and "attachment" not in str(
                part.get("Content-Disposition")
            ):
                html = part.get_payload(decode=True).decode()
                soup = BeautifulSoup(html, "html.parser")
                for script in soup(["script", "style"]):
                    script.decompose()  # Remove scripts and styles
                text = ' '.join(soup.stripped_strings)
        if not text:
            text = msg.get_payload(decode=True).decode()  # Fallback for any other types
    else:
        text = msg.get_payload(decode=True).decode()
    return text.strip() if text else None


def clean_email_body(body) -> str:
    # Remove extra whitespace and normalize the text
    body = " ".join(body.split())
    # Remove common footer patterns or unsubscribe links
    body = re.sub(
        r"\b(unsubscribe|click here|manage your subscription)\b",
        "",
        body,
        flags=re.IGNORECASE,
    )
    # Optionally remove URLs
    body = re.sub(r"http\S+", "", body)
    return body.lower()


def process_emails(emails) -> list[Any]:
    processed_emails = []
    for msg in emails:
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else "utf-8")

        body = get_body(msg)
        cleaned_body = clean_email_body(body)

        processed_emails.append({"subject": subject, "body": cleaned_body})

    return processed_emails
