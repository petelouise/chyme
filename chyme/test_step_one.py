import os
import imaplib
import email
from email import message
from email.header import decode_header
from dotenv import load_dotenv
import vcr
import pytest
from chyme.step_one import (
    connect_to_email,
    fetch_emails,
    get_body,
    clean_email_body,
    process_emails,
)

# Load environment variables
load_dotenv()

# Configure VCR
my_vcr = vcr.VCR(
    cassette_library_dir="fixtures/vcr_cassettes",
    record_mode="once",
    filter_headers=["authorization"],
    before_record_request=lambda request: request,
    before_record_response=lambda response: response,
)

# Helper function to create a mock email message
def create_mock_email(subject, body, content_type="text/plain"):
    msg = email.message.EmailMessage()
    msg["Subject"] = subject
    msg.set_content(body, subtype=content_type)
    return msg

@pytest.fixture
def email_credentials():
    return {
        "username": os.getenv("EMAIL_USERNAME"),
        "password": os.getenv("EMAIL_PASSWORD"),
        "receiving_email": os.getenv("RECEIVING_EMAIL")
    }

@my_vcr.use_cassette()
def test_connect_to_email(email_credentials):
    mail = connect_to_email(email_credentials["username"], email_credentials["password"])
    assert isinstance(mail, imaplib.IMAP4_SSL)
    mail.logout()

@my_vcr.use_cassette()
def test_fetch_emails(email_credentials):
    mail = connect_to_email(email_credentials["username"], email_credentials["password"])
    emails = fetch_emails(mail, email_credentials["receiving_email"], limit_emails=True)
    assert isinstance(emails, list)
    assert len(emails) > 0
    assert all(isinstance(email, message.Message) for email in emails)
    mail.logout()

def test_get_body():
    # Test with a plain text message
    plain_msg = create_mock_email("Test Subject", "Plain text content")
    assert get_body(plain_msg) == "Plain text content"

    # Test with an HTML message
    html_msg = create_mock_email("Test Subject", "<p>HTML content</p>", "text/html")
    assert get_body(html_msg).strip() == "HTML content"

    # Test with a multipart message
    multipart_msg = email.message.EmailMessage()
    multipart_msg.set_content("Plain text content")
    multipart_msg.add_alternative("<p>HTML content</p>", subtype="html")
    assert get_body(multipart_msg) == "Plain text content"

def test_clean_email_body():
    dirty_body = """
    This is a test email.

    Unsubscribe here: http://example.com/unsubscribe
    Click here to manage your subscription
    """
    clean_body = clean_email_body(dirty_body)
    assert "unsubscribe" not in clean_body.lower()
    assert "click here" not in clean_body.lower()
    assert "http://" not in clean_body
    assert "this is a test email" in clean_body.lower()

@my_vcr.use_cassette()
def test_process_emails(email_credentials):
    mail = connect_to_email(email_credentials["username"], email_credentials["password"])
    emails = fetch_emails(mail, email_credentials["receiving_email"], limit_emails=True)
    processed = process_emails(emails)
    assert isinstance(processed, list)
    assert len(processed) > 0
    assert all("subject" in email and "body" in email for email in processed)
    mail.logout()
