import email
from unittest.mock import Mock

import vcr

from step_one import (
    clean_email_body,
    connect_to_email,
    fetch_emails,
    get_body,
    process_emails,
)

# Use VCR to record and replay IMAP interactions
my_vcr = vcr.VCR(
    cassette_library_dir="fixtures/vcr_cassettes",
    record_mode="once",
    match_on=["uri", "method"],
)


@my_vcr.use_cassette()
def test_connect_to_email():
    mail = connect_to_email("test@example.com", "password")
    assert isinstance(mail, Mock)  # Because VCR will mock the IMAP connection


@my_vcr.use_cassette()
def test_fetch_emails():
    mail = connect_to_email("test@example.com", "password")
    emails = fetch_emails(mail, limit_emails=True)
    assert isinstance(emails, list)
    assert len(emails) > 0
    assert all(isinstance(email, email.message.Message) for email in emails)


def test_get_body():
    # Test with a multipart message
    multipart_msg = email.message.EmailMessage()
    multipart_msg.set_content("Plain text content")
    multipart_msg.add_alternative("<p>HTML content</p>", subtype="html")
    body = get_body(multipart_msg)
    assert body == "Plain text content"

    # Test with a simple message
    simple_msg = email.message.EmailMessage()
    simple_msg.set_content("Simple content")
    body = get_body(simple_msg)
    assert body == "Simple content"


def test_clean_email_body():
    dirty_body = """
    This is a test email.

    Unsubscribe here: http://example.com/unsubscribe
    Click here to manage your subscription
    """
    clean_body = clean_email_body(dirty_body)
    assert "unsubscribe" not in clean_body
    assert "click here" not in clean_body
    assert "http://" not in clean_body
    assert "this is a test email" in clean_body


@my_vcr.use_cassette()
def test_process_emails():
    mail = connect_to_email("test@example.com", "password")
    emails = fetch_emails(mail, limit_emails=True)
    processed = process_emails(emails)
    assert isinstance(processed, list)
    assert len(processed) > 0
    assert all("subject" in email and "body" in email for email in processed)
