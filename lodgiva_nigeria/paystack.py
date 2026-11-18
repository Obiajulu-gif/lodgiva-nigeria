"""Paystack, for Kamra's payment links.

Kamra asks a gateway for a hosted payment page and is told later that it was
paid. This module is Paystack's half of that conversation; it is claimed in
hooks.py (`kamra_payment_gateways`) so the Kamra fork never learns the name.

Settings come from the property's Payment Gateway Settings: `key_secret` is
the Paystack SECRET key (sk_live_... / sk_test_...). Paystack signs its
webhooks with that same key, so there is no separate webhook secret.

Webhook URL to register in the Paystack dashboard:
	https://<your-site>/api/method/lodgiva_nigeria.paystack.webhook
"""

import hashlib
import hmac
import json

import frappe
import requests

INITIALIZE = "https://api.paystack.co/transaction/initialize"


def create_link(settings, folio, guest, amount: float, currency: str) -> tuple[str, str]:
	"""(checkout url, reference) for one folio."""
	secret = settings.get_password("key_secret", raise_exception=False)
	if not secret:
		frappe.throw(
			"Paystack is selected but has no secret key. Add it under "
			"Payment Gateway Settings, or tick Test Mode to try the flow.")

	# Paystack will not open a transaction without a customer email, and a
	# walk-in often has none. The hotel's own address keeps the desk moving;
	# the receipt simply goes to the property instead of the guest.
	email = (guest.email or "").strip() or (
		frappe.db.get_value("Property", folio.property, "email") or "").strip()
	if not email:
		frappe.throw(
			"Paystack needs an email address to send the receipt to. Add one "
			"to the guest, or set the property's email under Settings.")

	reference = f"{folio.name}-{frappe.generate_hash(length=8)}"
	resp = requests.post(
		INITIALIZE,
		headers={"Authorization": f"Bearer {secret}"},
		json={
			"email": email,
			# Paystack counts in kobo.
			"amount": int(round(amount * 100)),
			"currency": currency,
			"reference": reference,
			"metadata": {"folio": folio.name, "reservation": folio.reservation},
		},
		timeout=20,
	)
	body = resp.json() if resp.content else {}
	if not body.get("status"):
		frappe.throw(f"Paystack refused the request: {body.get('message') or resp.status_code}")
	return body["data"]["authorization_url"], reference


@frappe.whitelist(allow_guest=True, methods=["POST"])
def webhook():
	"""Paystack calls this when a charge succeeds."""
	payload = frappe.request.get_data() or b"{}"
	event = json.loads(payload)
	data = event.get("data") or {}
	metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
	folio_name = metadata.get("folio")
	if event.get("event") != "charge.success" or not folio_name:
		return {"ignored": True}
	prop = frappe.db.get_value("Folio", folio_name, "property")
	if not prop:
		return {"ignored": True}

	from kamra.payments import _settings, post_link_payment

	settings = _settings(prop)
	secret = settings.get_password("key_secret", raise_exception=False) or ""
	given = frappe.get_request_header("x-paystack-signature") or ""
	expected = hmac.new(secret.encode(), payload, hashlib.sha512).hexdigest()
	# Checked before anything is believed: the body names its own folio, so
	# an unsigned request could otherwise mark any bill paid.
	if not secret or not hmac.compare_digest(given, expected):
		frappe.throw("Invalid webhook signature", frappe.PermissionError)

	# Paystack delivers the same event more than once, sometimes at the same
	# moment. The loser of the folio lock gets a lock conflict (MariaDB
	# snapshot isolation); retry it in a fresh transaction, where it sees
	# the winner's payment and answers 200 instead of a 500 Paystack would
	# keep retrying.
	for attempt in range(3):
		try:
			return _apply(folio_name, prop, data)
		except frappe.QueryDeadlockError:
			frappe.db.rollback()
			if attempt == 2:
				raise


def _apply(folio_name: str, prop: str, data: dict) -> dict:
	from kamra.payments import post_link_payment
	from lodgiva_nigeria.reconcile import record

	reference = data.get("reference") or ""
	amount = float(data.get("amount") or 0) / 100
	problem = mismatch(folio_name, prop, reference, data.get("currency") or "")
	if problem:
		# Signed, so it is real money - but not provably this folio's. Park
		# it for a human instead of crediting the wrong bill.
		record(prop, "Paystack", reference, amount, currency=data.get("currency") or "",
		       folio=folio_name, status="Unmatched", note=problem,
		       payer=(data.get("customer") or {}).get("email") or "")
		frappe.db.commit()  # nosemgrep: frappe-manual-commit -- persists before answering an external caller
		return {"ok": True, "folio": folio_name, "posted": False, "parked": problem}

	posted = post_link_payment(folio_name, amount, reference)
	record(prop, "Paystack", reference, amount, currency=data.get("currency") or "",
	       folio=folio_name, status="Matched",
	       note="Paystack webhook, posted." if posted else "Paystack retry, already posted.")
	frappe.db.commit()  # nosemgrep: frappe-manual-commit -- persists before answering an external caller
	return {"ok": True, "folio": folio_name, "posted": posted}


def mismatch(folio: str, property: str, reference: str, currency: str) -> str | None:
	"""Why a signed charge cannot be credited to `folio`, or None.

	create_link issues references as <folio>-<8 chars>, and asks for the
	property's currency. Anything else was not a link this folio issued."""
	from kamra.payments import _currency

	expected, _ = _currency(property)
	if (currency or "").upper() != expected.upper():
		return f"Paid in {currency or 'unknown currency'}, folio bills in {expected}."
	if not reference.startswith(f"{folio}-"):
		return f"Reference {reference} was not issued for {folio}."
	return None
