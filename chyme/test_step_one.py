import logging
import os

import pytest
import vcr
from dotenv import load_dotenv
from vcr.record_mode import RecordMode

from chyme.step_one import (
    clean_email_body,
    connect_to_email,
    fetch_emails,
    get_body,
    process_emails,
)

# Enable VCR debug logging
logging.basicConfig(level=logging.DEBUG)
vcr_log = logging.getLogger("vcr")
vcr_log.setLevel(logging.DEBUG)

# Ensure the cassette directory exists
cassette_dir = "tests/fixtures/vcr_cassettes"
os.makedirs(cassette_dir, exist_ok=True)

# Set up VCR
vcr_instance = vcr.VCR(
    cassette_library_dir=cassette_dir,
    record_mode=RecordMode.NEW_EPISODES,
    match_on=["uri", "method"],
    decode_compressed_response=True,
    filter_headers=["authorization"],
)

load_dotenv()

# Test data
TEST_USERNAME = os.environ["TEST_EMAIL_USERNAME"]
TEST_PASSWORD = os.environ["TEST_EMAIL_PASSWORD"]
TEST_RECEIVING_EMAIL = os.environ["TEST_RECEIVING_EMAIL"]


@vcr_instance.use_cassette()
def test_connect_to_email():
    mail = connect_to_email(TEST_USERNAME, TEST_PASSWORD)
    assert mail is not None
    assert mail.state == "AUTH"


@vcr_instance.use_cassette()
def test_fetch_emails():
    mail = connect_to_email(TEST_USERNAME, TEST_PASSWORD)
    emails = fetch_emails(mail, TEST_RECEIVING_EMAIL, limit_emails=True)
    assert isinstance(emails, list)
    assert len(emails) > 0


def test_get_body():
    # Test with a simple email message
    from email.message import EmailMessage

    msg = EmailMessage()
    msg.set_content("This is a test email body.")
    body = get_body(msg)
    assert body == "This is a test email body."


def test_clean_email_body():
    dirty_body = "Hello World! http://example.com Click here to Unsubscribe"
    clean_body = clean_email_body(dirty_body)
    assert "hello world!" in clean_body
    assert "http://" not in clean_body
    assert "unsubscribe" not in clean_body


@vcr_instance.use_cassette()
def test_process_emails():
    mail = connect_to_email(TEST_USERNAME, TEST_PASSWORD)
    emails = fetch_emails(mail, TEST_RECEIVING_EMAIL, limit_emails=True)
    processed = process_emails(emails)
    assert isinstance(processed, list)
    assert len(processed) > 0
    assert all("subject" in email and "body" in email for email in processed)


if __name__ == "__main__":
    pytest.main()
