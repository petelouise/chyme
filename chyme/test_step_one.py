import os
import sys

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

# Ensure the cassette directory exists
cassette_dir = "tests/fixtures/vcr_cassettes"
os.makedirs(cassette_dir, exist_ok=True)

def scrub_request(request):
    if 'authorization' in request.headers:
        del request.headers['authorization']
    return request

def scrub_response(response):
    if 'set-cookie' in response['headers']:
        del response['headers']['set-cookie']
    return response

# Set up VCR
vcr_instance = vcr.VCR(
    cassette_library_dir=cassette_dir,
    record_mode=RecordMode.ONCE,
    match_on=['uri', 'method', 'body'],
    filter_headers=['authorization', 'cookie'],
    decode_compressed_response=True,
    serializer='yaml',
    path_transformer=vcr.VCR.ensure_suffix('.yaml'),
    before_record_request=scrub_request,
    before_record_response=scrub_response,
)

load_dotenv()

# Test data
TEST_USERNAME = os.environ.get("TEST_EMAIL_USERNAME")
TEST_PASSWORD = os.environ.get("TEST_EMAIL_PASSWORD")
TEST_RECEIVING_EMAIL = os.environ.get("TEST_RECEIVING_EMAIL")

if not all([TEST_USERNAME, TEST_PASSWORD, TEST_RECEIVING_EMAIL]):
    print("Error: Missing required environment variables.")
    sys.exit(1)

@vcr_instance.use_cassette(path='tests/fixtures/vcr_cassettes/test_connect_to_email.yaml')
def test_connect_to_email():
    mail = connect_to_email(TEST_USERNAME, TEST_PASSWORD)
    assert mail is not None
    assert mail.state == "AUTH"

@vcr_instance.use_cassette(path='tests/fixtures/vcr_cassettes/test_fetch_emails.yaml')
def test_fetch_emails():
    mail = connect_to_email(TEST_USERNAME, TEST_PASSWORD)
    emails = fetch_emails(mail, TEST_RECEIVING_EMAIL, limit_emails=True)
    assert isinstance(emails, list)
    assert len(emails) > 0, "No emails were fetched"

def test_get_body():
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

@vcr_instance.use_cassette(path='tests/fixtures/vcr_cassettes/test_process_emails.yaml')
def test_process_emails():
    mail = connect_to_email(TEST_USERNAME, TEST_PASSWORD)
    emails = fetch_emails(mail, TEST_RECEIVING_EMAIL, limit_emails=True)
    processed = process_emails(emails)
    assert isinstance(processed, list)
    assert len(processed) > 0
    assert all("subject" in email and "body" in email for email in processed)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
