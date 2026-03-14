import logging
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_operation_notification(self, operation_id: str, event: str):
    """
    Send email/webhook notification when an operation changes state.
    Retries up to 3 times on failure.
    """
    try:
        logger.info("Sending %s notification for operation %s", event, operation_id)
        # TODO: integrate with your email provider (SendGrid, SES, etc.)
        # Example: send_email(to=..., subject=f"Operation {operation_id} {event}")
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3)
def generate_operation_pdf(self, operation_id: str):
    """
    Generate a PDF receipt/delivery note and upload to S3/R2.
    """
    try:
        logger.info("Generating PDF for operation %s", operation_id)
        # TODO: use reportlab or weasyprint to generate PDF
        # upload_to_s3(pdf_bytes, key=f"operations/{operation_id}.pdf")
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task
def daily_stock_check():
    """
    Nightly job: flag stock items with negative free-to-use quantities.
    Runs via Celery Beat at midnight UTC.
    """
    logger.info("Running daily stock check")
    # TODO: query stock_items where on_hand - reserved < 0 and alert
