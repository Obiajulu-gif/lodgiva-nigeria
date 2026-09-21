"""Lodgiva's financial controls over Kamra.

The 2026-09-21 vertical slice ran Kamra's Nigerian journey end to end and
found four money defects (docs/LODGIVA_GAP_MATRIX.md §8). Three of them are
fixed here rather than in the Kamra fork, so upgrading Kamra stays a merge:

  1. checkout let a guest depart owing money, balance untouched
  2. a folio still owing money could be closed and invoiced, with the debt
     going nowhere
  4. the same payment reference could post twice, driving a folio negative

Defect 3 (payment currency hard-defaulted to INR) is a schema default and is
fixed by the fixtures in `lodgiva_nigeria/fixtures/`, not by code.

Each control is enforced at the DOCUMENT level, not only on the whitelisted
API, because an internal python caller bypasses `override_whitelisted_methods`
entirely. A guard that only covers the HTTP route is not a guard.

Settlement can be waived deliberately - a company-billed stay is a real thing,
and so is a manager's judgement call - but never silently: see
`allow_unsettled_departure` on the Property.
"""

import frappe
from frappe import _


def _balance_for_reservation(reservation: str) -> float:
	"""Every open folio on the stay, not just the first. A split bill that
	hides a balance on a second folio is exactly how money walks out."""
	total = 0.0
	for f in frappe.get_all(
		"Folio",
		filters={"reservation": reservation},
		fields=["name", "balance", "status"],
	):
		total += float(f.balance or 0)
	return round(total, 2)


def _unsettled_departures_allowed(property_name: str) -> bool:
	try:
		return bool(frappe.db.get_value("Property", property_name, "allow_unsettled_departure"))
	except Exception:
		# Field not installed yet: default to the safe answer.
		return False


def reservation_before_save(doc, method=None):
	"""Refuse a departure that leaves money on the folio.

	Fires on Reservation.validate, so it holds for the REST route, the
	desk, a bench script and any future caller.
	"""
	if doc.status != "Checked Out":
		return

	before = doc.get_doc_before_save()
	if before is not None and before.status == "Checked Out":
		return  # already departed; this save is about something else

	balance = _balance_for_reservation(doc.name)
	if balance <= 0:
		return

	if _unsettled_departures_allowed(doc.property):
		# Allowed, but never silent - the audit trail is the whole point.
		doc.add_comment(
			"Comment",
			_("Checked out with an unsettled balance of {0}, permitted by property policy.").format(balance),
		)
		return

	frappe.throw(
		_(
			"{0} still owes {1} on this stay. Take payment, move the balance to a "
			"company or city-ledger folio, or post an allowance with a reason before "
			"checking out."
		).format(doc.guest_name or doc.name, balance),
		title=_("Bill not settled"),
	)


def folio_before_save(doc, method=None):
	"""Two controls on the folio itself.

	a) A folio carrying a balance cannot be closed and handed an invoice
	   number. Closing is what issues the invoice, and an invoice for money
	   nobody is chasing is worse than no invoice.
	b) The same payment reference cannot appear twice - a double-tapped
	   Pay button and a retried webhook both look like this.
	"""
	# (b) duplicate tender references
	seen = {}
	for row in doc.get("payments", []):
		ref = (row.get("reference") or "").strip().lower()
		if not ref:
			continue  # cash has no reference; nothing to dedupe on
		key = (row.get("mode"), ref)
		if key in seen:
			frappe.throw(
				_(
					"Reference {0} has already been recorded on this folio for {1}. "
					"If this is genuinely a second payment, give it its own reference."
				).format(row.get("reference"), row.get("mode")),
				title=_("Duplicate payment reference"),
			)
		seen[key] = True

	# (a) closing with a balance
	if doc.status != "Closed":
		return
	before = doc.get_doc_before_save()
	if before is not None and before.status == "Closed":
		return
	if float(doc.balance or 0) > 0 and not _unsettled_departures_allowed(doc.property):
		frappe.throw(
			_(
				"This folio still has a balance of {0}. Settle it, or move it to a "
				"company folio, before closing and issuing an invoice."
			).format(doc.balance),
			title=_("Cannot invoice an unsettled folio"),
		)
