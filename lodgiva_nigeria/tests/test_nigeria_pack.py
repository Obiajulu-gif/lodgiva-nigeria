"""Tests for the Nigeria localization pack that need no site or database.

The pack reads the property through `.get()`, so a plain dict stands in for
the Property doc. Run from the bench:

    env/bin/python -m unittest discover -s apps/lodgiva_nigeria -p "test_*.py" -v
"""

import unittest
from decimal import Decimal

from lodgiva_nigeria.localization import nigeria

LAGOS_HOTEL = {
	"name": "PROP-0001",
	"country": "Nigeria",
	"state": "Lagos",
	"city": "Ikeja",
	"currency": "NGN",
}

# Anything here in Nigerian output means an Indian assumption leaked through.
INDIAN_MARKERS = ("₹", "INR", "GST", "CGST", "SGST", "en-IN", "SAC", "Lakh", "Crore", "Rupee", "Paise")


class AmountInWords(unittest.TestCase):
	def test_naira_and_kobo(self):
		self.assertEqual(
			nigeria.amount_in_words(LAGOS_HOTEL, Decimal("12500.50")),
			"Naira Twelve Thousand Five Hundred and Fifty Kobo Only",
		)

	def test_whole_naira_has_no_kobo_clause(self):
		self.assertEqual(nigeria.amount_in_words(LAGOS_HOTEL, 1000), "Naira One Thousand Only")

	def test_international_grouping_not_lakh(self):
		# Kamra's shared helper defaults to Indian grouping; 2,500,000 must be
		# millions here, never "Twenty Five Lakh".
		self.assertEqual(
			nigeria.amount_in_words(LAGOS_HOTEL, 2_500_000),
			"Naira Two Million Five Hundred Thousand Only",
		)

	def test_zero_still_prints(self):
		self.assertEqual(nigeria.amount_in_words(LAGOS_HOTEL, 0), "Naira Zero Only")

	def test_negative_for_refunds(self):
		self.assertEqual(nigeria.amount_in_words(LAGOS_HOTEL, -150), "Minus Naira One Hundred Fifty Only")

	def test_half_kobo_rounds_up(self):
		self.assertEqual(
			nigeria.amount_in_words(LAGOS_HOTEL, Decimal("0.005")),
			"Naira Zero and One Kobo Only",
		)


class Labels(unittest.TestCase):
	def test_locale(self):
		loc = nigeria.locale(LAGOS_HOTEL)
		self.assertEqual(loc["currency_symbol"], "₦")
		self.assertEqual(loc["locale"], "en-NG")
		self.assertEqual(loc["currency"], "NGN")
		self.assertEqual(loc["tax_label"], "VAT")
		self.assertEqual(loc["tax_id_label"], "TIN")

	def test_locale_defaults_currency_to_naira(self):
		self.assertEqual(nigeria.locale({"name": "X"})["currency"], "NGN")

	def test_invoice_context(self):
		ctx = nigeria.invoice_context(LAGOS_HOTEL)
		self.assertEqual(ctx["tax_label"], "VAT")
		self.assertEqual(ctx["tax_id_label"], "TIN")
		self.assertIsNone(ctx["service_code"])
		self.assertEqual(ctx["place_of_supply"], "Lagos")

	def test_vat_is_one_line_never_halves(self):
		# India splits into CGST/SGST 50/50; Nigerian VAT is one federal line.
		self.assertEqual(nigeria.tax_split(LAGOS_HOTEL), [("vat", Decimal("1"))])
		self.assertEqual(nigeria.invoice_context(LAGOS_HOTEL)["split"], [("vat", Decimal("1"))])

	def test_no_service_code_per_line(self):
		self.assertIsNone(nigeria.service_code_for(LAGOS_HOTEL, "Room"))

	def test_no_indian_assumption_leaks_into_output(self):
		text = " ".join(
			str(v)
			for v in (
				*nigeria.locale(LAGOS_HOTEL).values(),
				*nigeria.invoice_context(LAGOS_HOTEL).values(),
				nigeria.amount_in_words(LAGOS_HOTEL, 2_500_000),
			)
		)
		for marker in INDIAN_MARKERS:
			self.assertNotIn(marker, text, f"Indian assumption {marker!r} leaked into Nigerian output")


class RoomTax(unittest.TestCase):
	def test_room_type_rate_wins_when_set(self):
		self.assertEqual(nigeria.calculate_room_tax("P", {"tax_percent": 10}, 50000), Decimal("10"))

	def test_unset_rate_uses_the_default(self):
		for unset in (None, 0, ""):
			self.assertEqual(
				nigeria.calculate_room_tax("P", {"tax_percent": unset}, 50000),
				Decimal("7.5"),
				f"tax_percent={unset!r}",
			)

	def test_no_room_type_uses_the_default(self):
		self.assertEqual(nigeria.calculate_room_tax("P", None, 50000), Decimal("7.5"))

	def test_rate_does_not_depend_on_tariff(self):
		# India picks a GST slab from the nightly tariff; Nigerian VAT does not.
		cheap = nigeria.calculate_room_tax("P", {"tax_percent": None}, 5_000)
		dear = nigeria.calculate_room_tax("P", {"tax_percent": None}, 500_000)
		self.assertEqual(cheap, dear)


class Registration(unittest.TestCase):
	def test_hook_claims_nigeria(self):
		# The whole design rests on this: Kamra resolves packs through the
		# merged `kamra_localization` hook, so this entry is what makes
		# Nigeria work without editing the Kamra fork.
		from lodgiva_nigeria import hooks

		self.assertEqual(
			hooks.kamra_localization.get("Nigeria"),
			"lodgiva_nigeria.localization.nigeria",
		)

	def test_depends_on_kamra(self):
		from lodgiva_nigeria import hooks

		self.assertIn("kamra", hooks.required_apps)


if __name__ == "__main__":
	unittest.main()
