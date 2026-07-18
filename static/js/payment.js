/**
 * payment.js — Razorpay checkout with automatic mock/demo mode support.
 *
 * When the backend returns `mock_mode: true`, a styled confirmation modal
 * is shown instead of launching the Razorpay SDK.
 */

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

async function startPayment(tripId) {
    const csrftoken = getCookie('csrftoken');

    const res = await fetch(`/pay/create/${tripId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json',
        },
    });

    const data = await res.json();

    // ── Mock / demo mode ─────────────────────────────────────────────────
    if (data.mock_mode) {
        showMockPaymentModal(data, csrftoken);
        return;
    }

    // ── Live Razorpay checkout ───────────────────────────────────────────
    const options = {
        key: data.key,
        amount: data.amount,
        currency: 'INR',
        order_id: data.order_id,
        name: 'TripMind AI',
        description: 'Trip Itinerary PDF Unlock',
        prefill: {
            name: data.name,
            email: data.email,
        },
        theme: {
            color: '#2563EB',
        },
        handler: async function (response) {
            const verifyRes = await fetch('/pay/verify/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    razorpay_order_id: response.razorpay_order_id,
                    razorpay_payment_id: response.razorpay_payment_id,
                    razorpay_signature: response.razorpay_signature,
                    trip_id: data.trip_id,
                }),
            });

            const result = await verifyRes.json();
            if (result.success) {
                window.location.href = result.redirect;
            } else {
                alert('Payment verification failed. Please contact support.');
            }
        },
    };

    const rzp = new Razorpay(options);
    rzp.open();
}


// ── Mock payment modal ───────────────────────────────────────────────────────

function showMockPaymentModal(data, csrftoken) {
    // Remove any existing modal
    const existing = document.getElementById('mock-payment-overlay');
    if (existing) existing.remove();

    const overlay = document.createElement('div');
    overlay.id = 'mock-payment-overlay';
    overlay.style.cssText = `
        position: fixed; inset: 0; z-index: 99999;
        display: flex; align-items: center; justify-content: center;
        background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(6px);
        animation: mockFadeIn 0.25s ease-out;
    `;

    overlay.innerHTML = `
        <style>
            @keyframes mockFadeIn {
                from { opacity: 0; }
                to   { opacity: 1; }
            }
            @keyframes mockSlideUp {
                from { opacity: 0; transform: translateY(24px) scale(0.96); }
                to   { opacity: 1; transform: translateY(0) scale(1); }
            }
            .mock-modal {
                background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
                border: 1px solid rgba(99, 102, 241, 0.3);
                border-radius: 20px;
                padding: 40px 36px 32px;
                max-width: 400px;
                width: 90%;
                text-align: center;
                color: #f1f5f9;
                font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
                box-shadow: 0 24px 48px rgba(0, 0, 0, 0.4),
                            0 0 0 1px rgba(99, 102, 241, 0.15) inset;
                animation: mockSlideUp 0.35s ease-out;
            }
            .mock-modal__badge {
                display: inline-block;
                background: linear-gradient(135deg, #f59e0b, #f97316);
                color: #1e293b;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1.2px;
                padding: 4px 14px;
                border-radius: 100px;
                margin-bottom: 20px;
            }
            .mock-modal__icon {
                font-size: 48px;
                margin-bottom: 12px;
            }
            .mock-modal__title {
                font-size: 22px;
                font-weight: 700;
                margin: 0 0 6px;
                background: linear-gradient(135deg, #818cf8, #6366f1);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .mock-modal__amount {
                font-size: 36px;
                font-weight: 800;
                margin: 16px 0;
                color: #e2e8f0;
            }
            .mock-modal__amount span {
                font-size: 20px;
                color: #94a3b8;
                font-weight: 500;
            }
            .mock-modal__desc {
                font-size: 14px;
                color: #94a3b8;
                margin-bottom: 28px;
                line-height: 1.5;
            }
            .mock-modal__btn {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background: linear-gradient(135deg, #6366f1, #4f46e5);
                color: #fff;
                border: none;
                border-radius: 12px;
                padding: 14px 32px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                width: 100%;
                justify-content: center;
            }
            .mock-modal__btn:hover {
                background: linear-gradient(135deg, #818cf8, #6366f1);
                transform: translateY(-1px);
                box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
            }
            .mock-modal__btn:active {
                transform: translateY(0);
            }
            .mock-modal__btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none !important;
                box-shadow: none !important;
            }
            .mock-modal__cancel {
                display: block;
                margin-top: 14px;
                background: none;
                border: none;
                color: #64748b;
                font-size: 13px;
                cursor: pointer;
                text-decoration: underline;
                text-underline-offset: 3px;
            }
            .mock-modal__cancel:hover {
                color: #94a3b8;
            }
            .mock-spinner {
                display: inline-block;
                width: 18px; height: 18px;
                border: 2px solid rgba(255,255,255,0.3);
                border-top-color: #fff;
                border-radius: 50%;
                animation: mockSpin 0.6s linear infinite;
            }
            @keyframes mockSpin {
                to { transform: rotate(360deg); }
            }
        </style>
        <div class="mock-modal">
            <div class="mock-modal__badge">Demo Mode</div>
            <div class="mock-modal__icon">🔓</div>
            <h3 class="mock-modal__title">Unlock Itinerary</h3>
            <div class="mock-modal__amount"><span>₹</span>99</div>
            <p class="mock-modal__desc">
                This is a simulated payment for demo purposes.<br>
                No real charges will be made.
            </p>
            <button class="mock-modal__btn" id="mock-pay-btn">
                ✓ Complete Payment
            </button>
            <button class="mock-modal__cancel" id="mock-cancel-btn">Cancel</button>
        </div>
    `;

    document.body.appendChild(overlay);

    // Cancel button
    document.getElementById('mock-cancel-btn').addEventListener('click', () => {
        overlay.remove();
    });

    // Close on backdrop click
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) overlay.remove();
    });

    // Complete payment button
    document.getElementById('mock-pay-btn').addEventListener('click', async () => {
        const btn = document.getElementById('mock-pay-btn');
        btn.disabled = true;
        btn.innerHTML = '<span class="mock-spinner"></span> Processing…';

        try {
            const verifyRes = await fetch('/pay/verify/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    razorpay_order_id: data.order_id,
                    razorpay_payment_id: 'mock_pay_' + Date.now(),
                    razorpay_signature: 'mock_signature',
                    trip_id: data.trip_id,
                }),
            });

            const result = await verifyRes.json();
            if (result.success) {
                btn.innerHTML = '✓ Payment Successful!';
                btn.style.background = 'linear-gradient(135deg, #22c55e, #16a34a)';
                setTimeout(() => {
                    window.location.href = result.redirect;
                }, 600);
            } else {
                btn.disabled = false;
                btn.innerHTML = '✓ Complete Payment';
                alert('Payment verification failed. Please try again.');
            }
        } catch (err) {
            btn.disabled = false;
            btn.innerHTML = '✓ Complete Payment';
            alert('Network error. Please try again.');
        }
    });
}
