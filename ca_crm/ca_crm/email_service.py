# services/email_service.py

from django.core.mail import EmailMessage
from django.conf import settings
from loguru import logger

def send_email(subject, body, to_emails, attachment=None, html_body=None):
    """
    Sends an email with optional attachment and HTML content.

    Args:
        subject (str): The subject of the email.
        body (str): The plain text body of the email.
        to_emails (list): List of recipient email addresses.
        attachment (tuple, optional): A tuple containing (filename, file_content, mime_type). Defaults to None.
        html_body (str, optional): The HTML body of the email. Defaults to None.

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """
    try:
        # Create the email message
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=to_emails,
        )

        # Attach HTML content if provided
        if html_body:
            email.content_subtype = 'html'  # Set content type to HTML
            email.body = html_body

        # Attach a file if provided
        if attachment:
            email.attach(attachment.name, attachment.read(), 'application/pdf')

        # Send the email
        email.send()
        logger.success(f"Email sent successfully to {to_emails}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_emails}. Error: {e}")
        return False