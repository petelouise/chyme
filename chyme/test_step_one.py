import os
import pytest
import vcr
from chyme.step_one import connect_to_email, fetch_emails, get_body, clean_email_body, process_emails

# Set up VCR
vcr = vcr.VCR(
    cassette_library_dir='tests/fixtures/vcr_cassettes',
    record_mode='once',
    match_on=['uri', 'method'],
)

# Test data
TEST_USERNAME = os.environ.get('TEST_EMAIL_USERNAME', 'test@example.com')
TEST_PASSWORD = os.environ.get('TEST_EMAIL_PASSWORD', 'password')
TEST_RECEIVING_EMAIL = os.environ.get('TEST_RECEIVING_EMAIL', 'receiver@example.com')

@vcr.use_cassette()
def test_connect_to_email():
    mail = connect_to_email(TEST_USERNAME, TEST_PASSWORD)
    assert mail is not None
    assert mail.state == 'AUTH'

@vcr.use_cassette()
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

@vcr.use_cassette()
def test_process_emails():
    mail = connect_to_email(TEST_USERNAME, TEST_PASSWORD)
    emails = fetch_emails(mail, TEST_RECEIVING_EMAIL, limit_emails=True)
    processed = process_emails(emails)
    assert isinstance(processed, list)
    assert len(processed) > 0
    assert all('subject' in email and 'body' in email for email in processed)

if __name__ == '__main__':
    pytest.main()
