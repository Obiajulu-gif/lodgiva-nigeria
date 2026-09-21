"""Nigerian defaults applied to Kamra's schema, without forking it.

Frappe lets one app retune another app's doctype through Property Setters and
Custom Fields. That is how Lodgiva ships Nigerian defaults while Kamra keeps
its Indian ones upstream - no merge conflicts when Kamra releases.

Applied on install and on every migrate, idempotently.

What this does NOT do: rename the `gst_rate` / `gst_amount` columns on Folio
Charge. Renaming a fieldname would break every Kamra query that reads them.
Their LABELS are retuned to VAT here; the column names remain a fork-edit
candidate, recorded in the gap matrix.
"""

import frappe

# doctype, fieldname, property, value, property_type
PROPERTY_SETTERS = [
	# The blank-country fallback in Kamra's pack_for() is India, so the
	# Property default is what quietly decides the tax regime.
	("Property", "country", "default", "Nigeria", "Text"),
	("Property", "currency", "default", "NGN", "Text"),
	("Property", "timezone", "default", "Africa/Lagos", "Text"),
	# Kamra's field is `gstin`; in Nigeria the number on an invoice is a TIN.
	("Property", "gstin", "label", "TIN", "Data"),
	# Defect 3 from the slice: a naira payment was stored as INR because the
	# Folio Payment currency is a Data field defaulted to INR.
	("Folio Payment", "currency", "default", "NGN", "Text"),
	# Nigerian tenders. UPI stays in the list on purpose: Kamra uses it as a
	# DEFAULT ARGUMENT in record_advance/record_payment, so removing the
	# option would make those calls fail validation. Recorded as fork work.
	(
		"Folio Payment",
		"mode",
		"options",
		"Cash\nBank Transfer\nPOS Terminal\nCard\nUPI\nOTA Prepaid\nCompany Credit\nPayment Link",
		"Text",
	),
	# Labels only - the fieldnames stay gst_* so Kamra's own queries work.
	("Folio Charge", "gst_rate", "label", "VAT Rate", "Data"),
	("Folio Charge", "gst_amount", "label", "VAT", "Data"),
]

CUSTOM_FIELDS = [
	{
		"dt": "Property",
		"fieldname": "allow_unsettled_departure",
		"label": "Allow departure with an unsettled balance",
		"fieldtype": "Check",
		"default": "0",
		"insert_after": "currency",
		"description": (
			"Off by default. When off, Lodgiva refuses to check a guest out, or to "
			"close and invoice a folio, while money is still owed. Turn it on only "
			"for a property that genuinely bills companies after departure - the "
			"departure is then recorded on the stay with a comment, never silently."
		),
	},
]


def apply_nigerian_defaults():
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	for doctype, fieldname, prop, value, prop_type in PROPERTY_SETTERS:
		if not frappe.db.exists("DocType", doctype):
			continue
		try:
			frappe.make_property_setter(
				{
					"doctype": doctype,
					"fieldname": fieldname,
					"property": prop,
					"value": value,
					"property_type": prop_type,
				},
				is_system_generated=False,
			)
		except Exception:
			frappe.log_error(title=f"Lodgiva property setter {doctype}.{fieldname}")

	by_doctype = {}
	for cf in CUSTOM_FIELDS:
		by_doctype.setdefault(cf["dt"], []).append({k: v for k, v in cf.items() if k != "dt"})
	create_custom_fields(by_doctype, update=True)

	frappe.db.commit()


def after_install():
	apply_nigerian_defaults()


def after_migrate():
	apply_nigerian_defaults()
