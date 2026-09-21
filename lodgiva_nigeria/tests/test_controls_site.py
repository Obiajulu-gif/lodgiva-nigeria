"""Do Lodgiva's controls actually stop what Kamra allowed on 2026-09-21?

Re-runs the exact three failures as tests. A control that is not exercised
against the original failure is decoration.
"""

import frappe

frappe.init(site="kamra.localhost")
frappe.connect()

from frappe.utils import add_days, nowdate  # noqa: E402
from kamra.api import (  # noqa: E402
	add_folio_payment,
	check_in,
	check_out,
	close_folio,
	create_booking,
	run_night_audit,
)

frappe.set_user("Administrator")
PROP = "Lodgiva Demo Hotel"

from kamra.business_date import get_business_date  # noqa: E402

# Earlier audits pushed the bench's business date past today; a stay must
# arrive ON the business date for the night audit to post its room charge.
BD = str(get_business_date(PROP))
print("BUSINESS_DATE", BD)
passed, failed = [], []


def expect_refused(label, fn):
	try:
		fn()
		frappe.db.commit()
		failed.append(label)
		print(f"  FAIL {label}: it went through")
	except Exception as e:
		frappe.db.rollback()
		passed.append(label)
		print(f"  PASS {label}: refused - {str(e)[:150]}")


def expect_ok(label, fn):
	try:
		out = fn()
		frappe.db.commit()
		passed.append(label)
		print(f"  PASS {label}: {str(out)[:120]}")
		return out
	except Exception as e:
		frappe.db.rollback()
		failed.append(label)
		print(f"  FAIL {label}: refused but should not be - {str(e)[:200]}")
		return None


print("=== defaults from the fixtures ===")
print("  Property.currency default:",
      frappe.db.get_value("Property Setter", {"doc_type": "Property", "field_name": "currency",
                                              "property": "default"}, "value"))
print("  Folio Payment.currency default:",
      frappe.db.get_value("Property Setter", {"doc_type": "Folio Payment", "field_name": "currency",
                                              "property": "default"}, "value"))
print("  tenders:", (frappe.db.get_value("Property Setter",
      {"doc_type": "Folio Payment", "field_name": "mode", "property": "options"}, "value") or "").split("\n"))

print("=== set up a stay that owes money ===")
res = expect_ok("book", lambda: create_booking(
	property=PROP, room_type=f"{PROP}-DLX",
	check_in_date=BD, check_out_date=add_days(BD, 1),
	guest_name="Ngozi Eze", phone="08055554444", adults=1, source="Manual",
))
if not res:
	raise SystemExit("no availability left on the demo property")
rn = res["reservation"]
expect_ok("check in", lambda: check_in(rn))
expect_ok("night audit posts the room night", lambda: run_night_audit(PROP))

folio = frappe.db.get_value("Folio", {"reservation": rn}, "name")
bal = frappe.db.get_value("Folio", folio, "balance")
print(f"  folio {folio} balance {bal}")
assert bal > 0, "expected an outstanding balance to test against"

print("=== defect 1: checkout while owing ===")
expect_refused("checkout is refused while money is owed", lambda: check_out(rn))

print("=== defect 2: closing and invoicing an unsettled folio ===")
expect_refused("close is refused while money is owed", lambda: close_folio(folio))

print("=== defect 4: the same reference twice ===")
expect_ok("first bank transfer", lambda: add_folio_payment(
	folio=folio, mode="Bank Transfer", amount=bal, reference="GTB/FT26092199001 Ngozi Eze"))
expect_refused("the same reference again is refused", lambda: add_folio_payment(
	folio=folio, mode="Bank Transfer", amount=1000, reference="GTB/FT26092199001 Ngozi Eze"))

print("=== defect 3: what currency did that payment store? ===")
for p in frappe.get_all("Folio Payment", filters={"parent": folio},
                        fields=["mode", "amount", "currency", "reference"]):
	print("  PAYMENT", dict(p))
	if p.currency != "NGN":
		failed.append(f"payment stored as {p.currency}")
	else:
		passed.append("payment stored in NGN")

print("=== the settled stay now departs normally ===")
expect_ok("checkout once settled", lambda: check_out(rn))
expect_ok("close once settled", lambda: close_folio(folio))
print("  invoice", frappe.db.get_value("Folio", folio, "invoice_number"),
      "balance", frappe.db.get_value("Folio", folio, "balance"))

print(f"\nRESULT passed={len(passed)} failed={len(failed)}")
for f in failed:
	print("  FAILED:", f)
print("J6_DONE")
