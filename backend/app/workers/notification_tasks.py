from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import structlog
from celery import Task

from app.core.config import settings
from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


class EmailTask(Task):  # type: ignore[type-arg]
    abstract = True

    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: object) -> None:
        logger.error("email_task_failed", task_id=task_id, error=str(exc))

    def on_retry(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: object) -> None:
        logger.warning("email_task_retry", task_id=task_id, error=str(exc))


def _send_smtp_email(to: str, subject: str, html_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        if settings.SMTP_TLS:
            smtp.starttls()
        if settings.SMTP_USERNAME:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.sendmail(settings.SMTP_FROM_EMAIL, to, msg.as_string())


@celery_app.task(
    base=EmailTask,
    bind=True,
    name="app.workers.notification_tasks.send_email_verification_task",
    max_retries=3,
    default_retry_delay=60,
)
def send_email_verification_task(
    self: Task,
    user_id: str,
    email: str,
    name: str,
    token: str,
) -> None:
    try:
        verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        html = f"""
        <h2>Verify your email address</h2>
        <p>Hello {name},</p>
        <p>Click the link below to verify your email address:</p>
        <a href="{verify_url}" style="
            background:#4F46E5;color:white;padding:12px 24px;
            text-decoration:none;border-radius:6px;display:inline-block;">
            Verify Email
        </a>
        <p>Link expires in 1 hour.</p>
        <p>If you did not register, ignore this email.</p>
        """
        _send_smtp_email(email, "Verify your email address", html)
        logger.info("email_verification_sent", user_id=user_id)
    except Exception as exc:
        logger.error("email_verification_failed", user_id=user_id, error=str(exc))
        raise self.retry(exc=exc) from exc


@celery_app.task(
    base=EmailTask,
    bind=True,
    name="app.workers.notification_tasks.send_password_reset_task",
    max_retries=3,
    default_retry_delay=60,
)
def send_password_reset_task(
    self: Task,
    user_id: str,
    email: str,
    name: str,
    token: str,
) -> None:
    try:
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        html = f"""
        <h2>Reset your password</h2>
        <p>Hello {name},</p>
        <p>Click the link below to reset your password:</p>
        <a href="{reset_url}" style="
            background:#EF4444;color:white;padding:12px 24px;
            text-decoration:none;border-radius:6px;display:inline-block;">
            Reset Password
        </a>
        <p>Link expires in 1 hour.</p>
        <p>If you did not request a password reset, ignore this email.</p>
        """
        _send_smtp_email(email, "Reset your password", html)
        logger.info("password_reset_email_sent", user_id=user_id)
    except Exception as exc:
        raise self.retry(exc=exc) from exc


@celery_app.task(
    base=EmailTask,
    bind=True,
    name="app.workers.notification_tasks.send_welcome_email_task",
    max_retries=3,
    default_retry_delay=60,
)
def send_welcome_email_task(self: Task, user_id: str, email: str, name: str) -> None:
    try:
        dashboard_url = f"{settings.FRONTEND_URL}/dashboard"
        html = f"""
        <h2>Welcome to {settings.APP_NAME}!</h2>
        <p>Hello {name},</p>
        <p>Your account has been verified and is now active.</p>
        <a href="{dashboard_url}" style="
            background:#4F46E5;color:white;padding:12px 24px;
            text-decoration:none;border-radius:6px;display:inline-block;">
            Go to Dashboard
        </a>
        """
        _send_smtp_email(email, f"Welcome to {settings.APP_NAME}!", html)
        logger.info("welcome_email_sent", user_id=user_id)
    except Exception as exc:
        raise self.retry(exc=exc) from exc


@celery_app.task(
    bind=True,
    name="app.workers.notification_tasks.send_reservation_notification_task",
    max_retries=3,
    default_retry_delay=30,
)
def send_reservation_notification_task(
    self: Task,
    event_type: str,
    reservation_id: str,
    tenant_id: str,
    customer_id: str,
) -> None:
    try:
        logger.info(
            "reservation_notification_queued",
            event_type=event_type,
            reservation_id=reservation_id,
        )
        # In a full implementation, fetch reservation details from DB and send email/SMS/push
        # This stub logs the event and marks success
    except Exception as exc:
        raise self.retry(exc=exc) from exc


@celery_app.task(
    bind=True,
    name="app.workers.notification_tasks.send_reminder_task",
    max_retries=3,
    default_retry_delay=60,
)
def send_reminder_task(
    self: Task,
    reservation_id: str,
    customer_email: str,
    customer_name: str,
    resource_name: str,
    start_time: str,
    hours_before: int,
) -> None:
    try:
        html = f"""
        <h2>Reminder: Upcoming Reservation</h2>
        <p>Hello {customer_name},</p>
        <p>You have a reservation in <strong>{hours_before} hour(s)</strong>:</p>
        <ul>
            <li><strong>Resource:</strong> {resource_name}</li>
            <li><strong>Time:</strong> {start_time}</li>
            <li><strong>Reference:</strong> #{reservation_id[:8].upper()}</li>
        </ul>
        """
        _send_smtp_email(customer_email, f"Reminder: Your reservation in {hours_before}h", html)
        logger.info("reminder_sent", reservation_id=reservation_id)
    except Exception as exc:
        raise self.retry(exc=exc) from exc
