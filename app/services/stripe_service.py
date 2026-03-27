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
        "price_id_annual": "price_1TFcdaPvTQyWBe6uIQN7Bp9u",
        "rate_limit": 500,
        "tier": "starter",
    },
    "pro": {
        "name": "LeadSolar Pro",
        "price_id": "price_1TFFdvPvTQyWBe6uMMD919W8",
        "price_id_annual": "price_1TFcdfPvTQyWBe6u0ycyMkYA",
        "rate_limit": 2000,
        "tier": "pro",
    },
    "enterprise": {
        "name": "LeadSolar Empresarial",
        "price_id": "price_1TFFdwPvTQyWBe6ucsHOsNWC",
        "price_id_annual": "price_1TFcdkPvTQyWBe6ulp0WJHqR",
        "rate_limit": 100000,
        "tier": "enterprise",
    },
}

BASE_URL = os.getenv("BASE_URL", "https://lead-intelligence-production.up.railway.app")


def _get_stripe():
    import stripe
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
    return stripe


def _get_db():
    try:
        import firebase_admin
        from firebase_admin import firestore
        if not firebase_admin._apps:
            return None
        return firestore.client()
    except Exception:
        return None


def generate_api_key() -> str:
    """Generate a secure API key for a new customer."""
    return "sk-ls-" + secrets.token_urlsafe(32)


# ──────────────────────────────────────────────
# Checkout
# ──────────────────────────────────────────────

def create_checkout_session(
    plan: str,
    customer_email: str | None = None,
    billing: str = "monthly",
) -> str:
    """Create a Stripe Checkout session and return the URL."""
    if plan not in PLANS:
        raise ValueError(f"Unknown plan: {plan}")

    stripe = _get_stripe()
    p = PLANS[plan]
    price_id = p["price_id_annual"] if billing == "annual" else p["price_id"]

    plan_name = p["name"]
    custom_submit = (
        f"Assinar {plan_name} — 30 dias grátis"
        if billing == "monthly"
        else f"Assinar {plan_name} anual — 30 dias grátis"
    )

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        subscription_data={"trial_period_days": 30},
        allow_promotion_codes=True,
        billing_address_collection="auto",
        phone_number_collection={"enabled": True},
        customer_email=customer_email,
        success_url=f"{BASE_URL}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{BASE_URL}/#precos",
        metadata={"plan": plan, "billing": billing},
        locale="pt-BR",
        custom_text={
            "submit": {"message": custom_submit},
            "after_submit": {
                "message": "Você receberá sua chave de API por aqui após confirmar. Suporte no WhatsApp: +55 91 99287-5776"
            },
        },
        consent_collection={"terms_of_service": "required"},
    )
    return session.url


# ──────────────────────────────────────────────
# Customer Portal (manage subscription)
# ──────────────────────────────────────────────

def create_portal_session(stripe_customer_id: str) -> str:
    """Create a Stripe Customer Portal session URL."""
    stripe = _get_stripe()
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=f"{BASE_URL}/#precos",
    )
    return session.url


def get_customer_by_email(email: str) -> dict[str, Any] | None:
    """Look up a customer in Firestore by email."""
    db = _get_db()
    if not db:
        return None
    docs = db.collection("customers").where("email", "==", email).limit(1).get()
    for doc in docs:
        return doc.to_dict()
    return None


# ──────────────────────────────────────────────
# Provisioning
# ──────────────────────────────────────────────

def provision_customer(session_id: str) -> dict[str, Any]:
    """
    After successful payment, create API key and store customer in Firestore.
    Idempotent — safe to call multiple times for same session.
    Returns customer info including the API key (shown once on first call).
    """
    stripe = _get_stripe()
    session = stripe.checkout.Session.retrieve(
        session_id,
        expand=["customer", "subscription"],
    )

    customer_email = session.get("customer_details", {}).get("email", "")
    plan = session.get("metadata", {}).get("plan", "pro")
    billing = session.get("metadata", {}).get("billing", "monthly")
    subscription_id = session.get("subscription", "")
    if hasattr(subscription_id, "id"):
        subscription_id = subscription_id.id

    stripe_customer_id = session.get("customer", "")
    if hasattr(stripe_customer_id, "id"):
        stripe_customer_id = stripe_customer_id.id

    # Idempotency — return existing if already provisioned
    db = _get_db()
    if db:
        existing = (
            db.collection("customers")
            .where("session_id", "==", session_id)
            .limit(1)
            .get()
        )
        docs = list(existing)
        if docs:
            data = docs[0].to_dict()
            return {**data, "already_provisioned": True}

    api_key = generate_api_key()
    plan_info = PLANS.get(plan, PLANS["pro"])

    customer_data = {
        "email": customer_email,
        "plan": plan,
        "billing": billing,
        "tier": plan_info["tier"],
        "api_key": api_key,
        "session_id": session_id,
        "subscription_id": subscription_id,
        "stripe_customer_id": stripe_customer_id,
        "status": "active",
        "created_at": datetime.now(UTC).isoformat(),
    }

    if db:
        db.collection("customers").add(customer_data)
        logger.info(
            "customer_provisioned email=%s plan=%s billing=%s",
            customer_email, plan, billing,
        )

    return {**customer_data, "already_provisioned": False}


# ──────────────────────────────────────────────
# Webhook
# ──────────────────────────────────────────────

def handle_webhook(payload: bytes, sig_header: str) -> str:
    """Process a Stripe webhook event. Returns event type string."""
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

    # ── Checkout completed → provision if not yet done (backup path) ──
    if event_type == "checkout.session.completed":
        obj = event["data"]["object"]
        session_id = obj.get("id", "")
        if session_id and db:
            existing = (
                db.collection("customers")
                .where("session_id", "==", session_id)
                .limit(1)
                .get()
            )
            if not list(existing):
                try:
                    provision_customer(session_id)
                    logger.info("webhook_provisioned session_id=%s", session_id)
                except Exception as exc:
                    logger.error("webhook_provision_failed session_id=%s error=%s", session_id, exc)

    # ── Subscription cancelled ──
    elif event_type == "customer.subscription.deleted":
        if not db:
            return event_type
        sub_id = event["data"]["object"]["id"]
        docs = (
            db.collection("customers")
            .where("subscription_id", "==", sub_id)
            .limit(1)
            .get()
        )
        for doc in docs:
            doc.reference.update({"status": "cancelled"})
            logger.info("subscription_cancelled sub_id=%s", sub_id)

    # ── Payment failed ──
    elif event_type == "invoice.payment_failed":
        if not db:
            return event_type
        sub_id = event["data"]["object"].get("subscription", "")
        if sub_id:
            docs = (
                db.collection("customers")
                .where("subscription_id", "==", sub_id)
                .limit(1)
                .get()
            )
            for doc in docs:
                doc.reference.update({"status": "past_due"})
                logger.info("payment_failed sub_id=%s", sub_id)

    # ── Subscription reactivated after past_due ──
    elif event_type == "invoice.paid":
        if not db:
            return event_type
        sub_id = event["data"]["object"].get("subscription", "")
        if sub_id:
            docs = (
                db.collection("customers")
                .where("subscription_id", "==", sub_id)
                .limit(1)
                .get()
            )
            for doc in docs:
                if doc.to_dict().get("status") == "past_due":
                    doc.reference.update({"status": "active"})
                    logger.info("subscription_reactivated sub_id=%s", sub_id)

    return event_type
