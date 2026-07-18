"""
services/email_svc.py — Email service with automatic mock/offline mode.

If the resend package is missing or RESEND_API_KEY is not configured,
emails are saved as JSON files in ``BASE_DIR/mock_emails/`` instead of
being dispatched through the Resend transactional email API.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

from django.conf import settings

logger = logging.getLogger('agent')

# ── Mock-mode detection ───────────────────────────────────────────────────────
MOCK_MODE = False

try:
    import resend

    if not os.environ.get('RESEND_API_KEY', ''):
        MOCK_MODE = True
        logger.warning(
            '[email] RESEND_API_KEY is empty — activating MOCK email mode. '
            'Emails will be saved to mock_emails/.'
        )
    else:
        logger.info('[email] Resend client ready (live mode).')
except ImportError:
    MOCK_MODE = True
    logger.warning(
        '[email] resend package not installed — activating MOCK email mode. '
        'Emails will be saved to mock_emails/.'
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_html(trip, user_name: str) -> str:
    """Build the itinerary email HTML body."""
    total_cost = trip.total_estimated_cost
    return (
        f"<div style=\"font-family: 'Inter', Arial, sans-serif; max-width: 600px; "
        f"margin: 0 auto; padding: 24px;\">"
        f"<h2 style=\"color: #2563EB;\">✈ TripMind AI</h2>"
        f"<p>Hi {user_name},</p>"
        f"<p>Your <strong>{trip.num_days}-day {trip.destination}</strong> itinerary is ready!</p>"
        f"<p>Estimated total cost: <strong>₹{total_cost:,}</strong></p>"
        f"<p>Your detailed day-by-day plan is attached as a PDF.</p>"
        f"<br>"
        f"<p>Happy travels! 🌍</p>"
        f"<p style=\"color: #64748B;\">— TripMind AI</p>"
        f"</div>"
    )


# ── Public API ────────────────────────────────────────────────────────────────

def send_itinerary_email(to_email: str, trip, pdf_path: str) -> bool:
    """Send itinerary PDF via Resend email service.

    In mock mode the email payload is saved as a JSON file in
    ``BASE_DIR/mock_emails/`` and ``True`` is returned to simulate success.
    """
    user_name = trip.user.first_name or trip.user.email
    attachment_filename = f'{trip.destination}_itinerary.pdf'
    html_body = _build_html(trip, user_name)
    subject = f'Your {trip.destination} Itinerary is Ready ✈'

    # ── Mock path ─────────────────────────────────────────────────────────
    if MOCK_MODE:
        try:
            mock_dir = Path(settings.BASE_DIR) / 'mock_emails'
            mock_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{trip.pk}_{timestamp}.json'
            filepath = mock_dir / filename

            payload = {
                'to': to_email,
                'subject': subject,
                'html_body': html_body,
                'attachment_filename': attachment_filename,
                'sent_at': datetime.now().isoformat(),
            }

            filepath.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
            logger.info(
                f'[email] Mock email saved locally: {filepath} '
                f'(to={to_email}, trip={trip.pk})'
            )
            return True
        except Exception as e:
            logger.error(f'[email] Failed to save mock email: {e}')
            return False

    # ── Live path ─────────────────────────────────────────────────────────
    try:
        resend.api_key = os.environ.get('RESEND_API_KEY', '')
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        resend.Emails.send({
            'from': os.environ.get('FROM_EMAIL', 'trips@tripmind.ai'),
            'to': [to_email],
            'subject': subject,
            'html': html_body,
            'attachments': [{
                'filename': attachment_filename,
                'content': list(pdf_bytes),
            }],
        })
        logger.info(f'[email] Email sent to {to_email} for trip {trip.pk}')
        return True
    except Exception as e:
        logger.error(f'[email] Email send error: {e}')
        return False
