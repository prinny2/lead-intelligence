"""Stripe integration — checkout sessions, webhook handling, subscription management."""

from __future__ import annotations

import logging
import os
import secrets
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("lead_intelligence.stripe")

PLANS = {
    "starter": {
        "name": "LeadSolar Starter",
        "price_id": "price_1TFFdtPvTQyWBe6uIdY737DH",
        "rate_limit": 500,
        "tier": "starter",
    },
    "pro": {
        "name": "LeadSolar Pro",
        "price_id": "price_1TFFdvPvTQyWBe6uMMD919W8",
        "rate_limit": 2000,
        "tier": "pro",
    },
    "enterprise": {
        "name": "LeadSolar Empresarial",
        "price_id": "price_1TFFdwPvTQyWBe6ucsHOsNWC",
        "rate_limit": 100000,
        "tier": "enterprise",
    },
}

BASE_URL = os.getenv("BASE_URL", "https://lead-intelligence-production.up.railway.app")


def _get_stripe():
    import stripe
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
    return stripe


def create_checkout_session(plan: str, customer_email: str | None = None) -> str:
    """Create a Stripe Checkout session and return the URL."""
    if plan not in PLANS:
        raise ValueError(f"Unknown plan: {plan}")

    stripe = _get_stripe()
    p = PLANS[plan]

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": p["price_id"], "quantity": 1}],
        subscription_data={"trial_period_days": 30},
        customer_email=customer_email,
        success_url=f"{BASE_URL}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{BASE_URL}/#precos",
        metadata={"plan": plan},
        locale="pt-BR",
    )
    return session.url


def get_session(session_id: str) -> dict[str, Any]:
    """Retrieve a checkout session."""
    stripe = _get_stripe()
    return stripe.checkout.Session.retrieve(session_id)


def generate_api_key() -> str:
    """Generate a secure API key for a new customer."""
    return "sk-ls-" + secrets.token_urlsafe(32)


def _get_db():
    try:
        import firebase_admin
        from firebase_admin import firestore
        if not firebase_admin._apps:
            return None
        return firestore.client()
    except Exception:
        return None


def provision_customer(session_id: str) -> dict[str, Any]:
    """
    After successful payment, create API key and store customer in Firestore.
    Returns customer info including the API key (shown once).
    """
    stripe = _get_stripe()
    session = stripe.checkout.Session.retrieve(session_id, expand=["customer"])

    customer_email = session.get("customer_details", {}).get("email", "")
    plan = session.get("metadata", {}).get("plan", "pro")
    subscription_id = session.get("subscription", "")

    # Check if already provisioned
    db = _get_db()
    if db:
        existing = db.collection("customers").where("session_id", "==", session_id).limit(1).get()
        if list(existing):
            doc = list(existing)[0]
            data = doc.to_dict()
            return {"already_provisioned": True, "email": data.get("email", ""), "plan": plan}

    api_key = generate_api_key()
    customer_data = {
        "email": customer_email,
        "plan": plan,
        "tier": PLANS[plan]["tier"],
        "api_key": api_key,
        "session_id": session_id,
        "subscription_id": subscription_id,
        "status": "active",
        "created_at": datetime.now(UTC).isoformat(),
    }

    if db:
        db.collection("customers").add(customer_data)
        logger.info("customer_provisioned email=%s plan=%s", customer_email, plan)

    return {**customer_data, "already_provisioned": False}


def handle_webhook(payload: bytes, sig_header: str) -> str:
    """Process a Stripe webhook event. Returns event type."""
    stripe = _get_stripe()
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    if webhook_secret:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    else:
        import json
        event = json.loads(payload)

    event_type = event.get("type", "")
    logger.info("stripe_webhook event=%s", event_type)

    db = _get_db()
    if not db:
        return event_type

    if event_type == "customer.subscription.deleted":
        sub_id = event["data"]["object"]["id"]
        docs = db.collection("customers").where("subscription_id", "==", sub_id).limit(1).get()
        for doc in docs:
            doc.reference.update({"status": "cancelled"})
            logger.info("subscription_cancelled sub_id=%s", sub_id)

    elif event_type == "invoice.payment_failed":
        sub_id = event["data"]["object"].get("subscription", "")
        if sub_id:
            docs = db.collection("customers").where("subscription_id", "==", sub_id).limit(1).get()
            for doc in docs:
                doc.reference.update({"status": "past_due"})
                logger.info("payment_failed sub_id=%s", sub_id)

    return event_type
