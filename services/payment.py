"""
services/payment.py — Razorpay payment service with automatic mock/offline mode.

If the razorpay package is missing or RAZORPAY_KEY_ID is not configured,
mock mode activates automatically, returning simulated orders and approving
all verifications for mock order IDs.
"""

import os
import hmac
import hashlib
import logging
from uuid import uuid4

logger = logging.getLogger('agent')

# ── Mock-mode detection ───────────────────────────────────────────────────────
MOCK_MODE = False
_rz = None

try:
    import razorpay

    _key_id = os.environ.get('RAZORPAY_KEY_ID', '')
    _key_secret = os.environ.get('RAZORPAY_KEY_SECRET', '')

    if not _key_id:
        MOCK_MODE = True
        logger.warning(
            '[payment] RAZORPAY_KEY_ID is empty — activating MOCK payment mode.'
        )
    else:
        _rz = razorpay.Client(auth=(_key_id, _key_secret))
        logger.info('[payment] Razorpay client initialised (live mode).')
except ImportError:
    MOCK_MODE = True
    logger.warning(
        '[payment] razorpay package not installed — activating MOCK payment mode.'
    )


# ── Public API ────────────────────────────────────────────────────────────────

def create_order(amount_inr: int = 99) -> dict:
    """Create a Razorpay order (or a mock order in offline mode)."""
    if MOCK_MODE:
        order = {
            'id': f'mock_order_{uuid4().hex[:12]}',
            'amount': amount_inr * 100,
            'currency': 'INR',
        }
        logger.info(f'[payment] Mock order created: {order["id"]}')
        return order

    return _rz.order.create({
        'amount': amount_inr * 100,
        'currency': 'INR',
        'payment_capture': 1,
    })


def verify_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verify Razorpay payment signature using HMAC SHA256.

    Mock orders (ID starting with ``mock_order_``) are auto-approved.
    """
    if MOCK_MODE or order_id.startswith('mock_order_'):
        logger.info(f'[payment] Mock signature verification — auto-approved for {order_id}')
        return True

    secret = os.environ.get('RAZORPAY_KEY_SECRET', '').encode()
    message = f'{order_id}|{payment_id}'.encode()
    expected = hmac.new(secret, message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
