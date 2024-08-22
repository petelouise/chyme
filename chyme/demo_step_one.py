import os

from dotenv import load_dotenv

from chyme.step_one import connect_to_email, fetch_emails, process_emails

load_dotenv()


def main(username, password, receiving_email) -> None:
    mail = connect_to_email(username, password)
    emails = fetch_emails(mail, receiving_email, limit_emails=True)
    processed_emails = process_emails(emails)

    # Output the processed emails for review
    for femail in processed_emails:
        print(f"Subject: {femail['subject']}")
        print(f"Body: {femail['body']}\n")

    mail.logout()


if __name__ == "__main__":
    # Email server credentials
    username = os.getenv("EMAIL_USERNAME")
    password = os.getenv("EMAIL_PASSWORD")
    receiving_email = os.getenv("RECEIVING_EMAIL")

    main(username, password, receiving_email)
