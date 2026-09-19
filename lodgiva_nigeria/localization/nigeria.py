"""Nigeria localization pack for Lodgiva PMS (built on Kamra).

Claimed through Kamra's `kamra_localization` hook, so no line of the Kamra
fork changes to add Nigeria - see lodgiva_nigeria/hooks.py.

Tax model, deliberately following Kamra's UAE pack rather than the Indian one:

  - VAT is a single federal line. 7.5% is a CONFIGURABLE DEFAULT for the
    first vertical slice, not tax advice; the rate comes from the Room Type's
    tax percent when one is set. Confirm with a tax adviser before go-live.
  - Service charge is the hotel's own charge, not a tax, and state or local
    consumption levies (for example a state hotel consumption tax) are not
    shares of the VAT rate. Like the UAE's municipality fee and service
    charge, they belong on the folio as separate lines - never folded into
    the VAT split, which would print a service charge as if it were tax.

Everything here reads the property doc through `.get()`, so the pure helpers
(labels, words, locale) can be exercised without a database.
"""

from decimal import ROUND_HALF_UP, Decimal

import frappe

DEFAULT_VAT = Decimal("7.5")
CURRENCY = "NGN"
SYMBOL = "₦"  # ₦


def calculate_room_tax(property, room_type_doc, nightly_rate) -> Decimal:
	"""VAT rate for one room night: the room type's percent when set,
	otherwise the Nigerian default.

	Mirrors the UAE pack: an unset (or zero) room-type percent means "use the
	default". A genuinely VAT-exempt room cannot be expressed this way yet -
	recorded as a gap rather than papered over.
	"""
	v = room_type_doc.get("tax_percent") if room_type_doc else None
	return Decimal(str(v)) if v else DEFAULT_VAT


def fnb_tax_rate(property) -> float:
	"""Hotel food and beverage is the same standard-rated VAT supply."""
	return float(DEFAULT_VAT)


def tax_rate_options(property) -> list:
	return [0, 7.5]


def invoice_context(prop_doc) -> dict:
	return {
		"tax_label": "VAT",
		"tax_id_label": "TIN",
		# Nigeria has no SAC/HSN-style per-line service code to print.
		"service_code": None,
		"sac": None,
		"place_of_supply": prop_doc.get("state") or prop_doc.get("city"),
		"split": [("vat", Decimal("1"))],
		"footer": (
			"Service charge and any state consumption levy appear as separate "
			"lines and are not VAT. This is a computer-generated invoice."
		),
	}


def service_code_for(prop_doc, charge_type=None):
	return None


def tax_split(prop_doc, buyer_tax_id=None):
	"""One federal VAT line. Deliberately never CGST/SGST-style halves."""
	return [("vat", Decimal("1"))]


def amount_in_words(prop_doc, amount) -> str:
	"""'Naira Twelve Thousand Five Hundred and Fifty Kobo Only'.

	Kamra's shared helper has no NGN entry and would print "NGN Twelve
	Only" with the kobo dropped, so the pack spells it itself using the
	international grouping (thousand, million) Nigerian invoices use.
	"""
	from kamra.localization.words import number_in_words

	value = Decimal(str(amount or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
	negative = value < 0
	value = abs(value)
	naira = int(value)
	kobo = int((value - naira) * 100)
	words = f"Naira {number_in_words(naira, indian=False)}"
	if kobo:
		words += f" and {number_in_words(kobo, indian=False)} Kobo"
	if negative:
		words = "Minus " + words
	return f"{words} Only"


def locale(prop_doc) -> dict:
	return {
		"currency_symbol": SYMBOL,
		"locale": "en-NG",
		"currency": prop_doc.get("currency") or CURRENCY,
		"tax_label": "VAT",
		"tax_id_label": "TIN",
		"tax_rates": [0, 7.5],
	}
