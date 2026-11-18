"""Reconciliation queue: money seen outside the PMS, matched to folios.

Nigerian hotels take most money three ways the PMS never sees directly:
bank transfers (the guest's narration may or may not quote the booking),
POS terminal slips, and Paystack settlements. Each line from a bank
statement, a terminal batch or a Paystack export becomes a Payment Match
row, and is matched to a folio automatically when the evidence is clear:

- Matched:   the money is already on the folio (same reference, or the desk
             recorded the same amount by the same tender).
- Suggested: a folio was found (booking/folio number in the narration, or a
             Paystack reference) but the money is not on it yet. A finance
             user confirms with Post.
- Unmatched: nothing to go on, or the currency/property disagrees.

Resolution (post / match / ignore) needs a note and records who did it.
`export` is the daily accounting file: every payment on the date, with its
reconciliation status.
"""

import csv
import io
import json
import re

import frappe
from frappe.utils import flt, getdate, now_datetime, nowdate

from kamra.authz import require_roles

# Folio Payment modes each source can appear as. The Nigeria pack adds a
# "POS Terminal" tender; sites without it record terminal payments as Card.
MODES = {"Bank Transfer": ("Bank Transfer",), "POS Terminal": ("POS Terminal", "Card"),
         "Paystack": ("Payment Link",)}


def _post_mode(source: str) -> str:
	options = (frappe.get_meta("Folio Payment").get_field("mode").options or "").splitlines()
	return next((m for m in MODES[source] if m in options), MODES[source][-1])


DOC_REF = re.compile(r"\b((?:FOLIO|RES)-\d{4}-\d{3,})\b", re.I)
OPEN = ("Unmatched", "Suggested")


def find_folio(property: str, source: str, reference: str, narration: str = "") -> str | None:
	"""The folio this payment names, if it names one on this property."""
	text = f"{reference} {narration}"
	candidates = []
	if source == "Paystack" and "-" in reference:
		candidates.append(reference.rsplit("-", 1)[0])  # paystack.create_link: <folio>-<hash>
	candidates += [m.upper() for m in DOC_REF.findall(text)]
	for c in candidates:
		if frappe.db.get_value("Folio", c, "property") == property:
			return c
		if c.startswith("RES-"):
			folio = frappe.db.get_value(
				"Folio", {"reservation": c, "folio_type": "Guest", "property": property}, "name")
			if folio:
				return folio
	return None


def _payment_on_folio(folio: str, source: str, reference: str, amount: float) -> str | None:
	"""A Folio Payment row that already accounts for this money."""
	rows = frappe.db.sql(
		"""select name, reference, amount, mode from `tabFolio Payment`
		   where parenttype='Folio' and parent=%s""", folio, as_dict=True)
	for r in rows:
		if reference and r.reference == reference:
			return r.name
	claimed = set(frappe.get_all("Payment Match", filters={"folio": folio, "status": "Matched"},
	                             pluck="match_note"))
	for r in rows:
		if (r.mode in MODES[source] and abs(flt(r.amount) - amount) < 0.01
				and not any(r.name in (c or "") for c in claimed)):
			return r.name
	return None


def auto_match(doc) -> None:
	"""Set status / folio / match_note on a Payment Match from the evidence."""
	from kamra.payments import _currency
	currency, _ = _currency(doc.property)
	if doc.currency and doc.currency.upper() != currency.upper():
		doc.status, doc.match_note = "Unmatched", f"Currency {doc.currency} is not {currency}."
		return
	folio = doc.folio or find_folio(doc.property, doc.source, doc.reference, doc.narration or "")
	if not folio:
		doc.status, doc.match_note = "Unmatched", "No folio or booking number found."
		return
	doc.folio = folio
	row = _payment_on_folio(folio, doc.source, doc.reference, flt(doc.amount))
	if row:
		doc.status, doc.match_note = "Matched", f"Already on {folio} (payment row {row})."
	else:
		doc.status, doc.match_note = "Suggested", f"{folio} named, money not on it yet."


def record(property: str, source: str, reference: str, amount: float, *, currency: str = "",
           received_on=None, payer: str = "", narration: str = "", folio: str | None = None,
           status: str | None = None, note: str = "") -> tuple[str, bool]:
	"""Add one line to the queue (auto-matched). (name, created) - a line
	already in the queue (same source and reference) is not added twice."""
	key = f"{source}:{(reference or '').strip()}"
	existing = frappe.db.get_value("Payment Match", {"match_key": key})
	if existing:
		return existing, False
	doc = frappe.get_doc({
		"doctype": "Payment Match", "property": property, "source": source,
		"reference": reference, "amount": flt(amount), "currency": currency,
		"received_on": getdate(received_on or nowdate()), "payer": payer,
		"narration": narration, "folio": folio,
	})
	if status:
		doc.status, doc.match_note = status, note
	else:
		auto_match(doc)
	try:
		doc.insert(ignore_permissions=True)
	except frappe.DuplicateEntryError:
		# a concurrent delivery of the same payment won the unique match_key
		return frappe.db.get_value("Payment Match", {"match_key": key}, for_update=True), False
	return doc.name, True


def _rows(rows) -> list[dict]:
	if isinstance(rows, str):
		rows = rows.strip()
		if rows.startswith("["):
			return json.loads(rows)
		return list(csv.DictReader(io.StringIO(rows)))
	return rows or []


@frappe.whitelist(methods=["POST"])
@require_roles("Finance", "Hotel Admin")
def ingest(property: str, source: str, rows) -> dict:
	"""Load a bank statement / terminal batch / Paystack export.

	rows: JSON list or CSV text with columns reference, amount, and
	optionally date, payer, narration, currency."""
	if source not in MODES:
		frappe.throw(f"Source must be one of {', '.join(MODES)}.")
	added = skipped = 0
	counts = {s: 0 for s in ("Unmatched", "Suggested", "Matched")}
	for r in _rows(rows):
		ref, amount = (r.get("reference") or "").strip(), flt(r.get("amount"))
		if not ref or amount <= 0:
			skipped += 1
			continue
		name, created = record(property, source, ref, amount, currency=r.get("currency") or "",
		                       received_on=r.get("date"), payer=r.get("payer") or "",
		                       narration=r.get("narration") or "")
		if created:
			added += 1
			counts[frappe.db.get_value("Payment Match", name, "status")] += 1
		else:
			skipped += 1
	return {"added": added, "skipped": skipped, **counts}


@frappe.whitelist()
@require_roles("Finance", "Hotel Admin", "Front Desk")
def queue(property: str | None = None, status: str | None = None, limit: int = 200) -> list:
	from kamra.api import my_properties
	allowed = [p["name"] for p in my_properties()]
	filters = {"property": ["in", [property] if property in allowed else allowed]}
	filters["status"] = ["in", OPEN] if not status else status
	return frappe.get_all(
		"Payment Match", filters=filters,
		fields=["name", "property", "source", "reference", "amount", "currency", "received_on",
		        "status", "folio", "payer", "narration", "match_note", "resolved_by",
		        "resolved_on", "resolution_note"],
		order_by="received_on desc, creation desc", limit=int(limit))


@frappe.whitelist(methods=["POST"])
@require_roles("Finance", "Hotel Admin")
def resolve(name: str, action: str, note: str, folio: str | None = None) -> dict:
	"""post: put the money on the folio. match: it is already there.
	ignore: not hotel money (a refund bounce, a personal transfer...)."""
	if not (note or "").strip():
		frappe.throw("A resolution needs a note - it goes on the record.")
	doc = frappe.get_doc("Payment Match", name)
	from kamra.crs import assert_property_access
	assert_property_access(doc.property)
	if doc.status not in OPEN:
		frappe.throw(f"This payment is already {doc.status}.")
	folio = folio or doc.folio
	if action in ("post", "match"):
		if not folio or frappe.db.get_value("Folio", folio, "property") != doc.property:
			frappe.throw("Pick a folio of this property.")
		doc.folio = folio
	if action == "post":
		from kamra.payments import post_link_payment
		if not post_link_payment(folio, flt(doc.amount), doc.reference, mode=_post_mode(doc.source)):
			frappe.throw("That reference is already on the folio - use Match instead.")
		doc.status = "Resolved"
		doc.match_note = f"Posted to {folio} by reconciliation."
	elif action == "match":
		doc.status = "Matched"
		doc.match_note = f"Confirmed on {folio} by hand."
	elif action == "ignore":
		doc.status = "Ignored"
	else:
		frappe.throw("action must be post, match or ignore.")
	doc.resolved_by, doc.resolved_on = frappe.session.user, now_datetime()
	doc.resolution_note = note.strip()
	doc.save(ignore_permissions=True)
	doc.add_comment("Info", f"{action} by {frappe.session.user}: {note.strip()}")
	return {"name": doc.name, "status": doc.status, "folio": doc.folio}


@frappe.whitelist()
@require_roles("Finance", "Hotel Admin")
def export(property: str, date: str | None = None):
	"""Daily accounting export (CSV download): every payment posted on the
	date, plus queue lines received that day that never reached a folio."""
	date = str(getdate(date or nowdate()))
	matched = {}
	for m in frappe.get_all("Payment Match", filters={"property": property, "folio": ["is", "set"]},
	                        fields=["folio", "reference", "status", "name"]):
		matched[(m.folio, m.reference)] = m
	buf = io.StringIO()
	w = csv.writer(buf)
	w.writerow(["date", "property", "folio", "guest", "mode", "kind", "amount", "reference",
	            "reconciliation", "queue_id"])
	for p in frappe.db.sql(
			"""select fp.posting_date, f.name folio, f.guest_name, fp.mode, fp.payment_kind,
			          fp.amount, fp.reference
			   from `tabFolio Payment` fp join `tabFolio` f on f.name=fp.parent and fp.parenttype='Folio'
			   where f.property=%s and fp.posting_date=%s order by f.name""",
			(property, date), as_dict=True):
		m = matched.get((p.folio, p.reference))
		w.writerow([p.posting_date, property, p.folio, p.guest_name, p.mode, p.payment_kind,
		            p.amount, p.reference or "", m.status if m else "Desk", m.name if m else ""])
	for m in frappe.get_all("Payment Match", filters={"property": property, "received_on": date,
	                                                   "status": ["in", OPEN + ("Ignored",)]},
	                        fields=["name", "source", "amount", "reference", "status", "folio"]):
		w.writerow([date, property, m.folio or "", "", m.source, "Not posted", m.amount,
		            m.reference, m.status, m.name])
	frappe.response["type"] = "download"
	frappe.response["filename"] = f"payments-{property}-{date}.csv".replace(" ", "_")
	frappe.response["filecontent"] = buf.getvalue()
	frappe.response["content_type"] = "text/csv"
