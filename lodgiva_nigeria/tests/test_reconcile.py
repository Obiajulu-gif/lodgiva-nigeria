"""Matching rules for the reconciliation queue and Paystack webhooks.

Run with: bench --site <hotel site> run-tests --app lodgiva_nigeria \
    --module lodgiva_nigeria.tests.test_reconcile
"""

import unittest
from unittest.mock import patch

from lodgiva_nigeria import paystack, reconcile

FOLIOS = {"FOLIO-2026-00012": "Hotel A", "FOLIO-2026-00099": "Hotel B"}


def fake_get_value(doctype, filters, field=None, *a, **k):
	if doctype == "Folio" and isinstance(filters, str):
		return FOLIOS.get(filters)
	if doctype == "Folio" and isinstance(filters, dict) and filters.get("reservation") == "RES-2026-00007":
		return "FOLIO-2026-00012" if filters.get("property") == "Hotel A" else None
	return None


class TestFindFolio(unittest.TestCase):
	def find(self, *args):
		with patch("frappe.db.get_value", side_effect=fake_get_value):
			return reconcile.find_folio(*args)

	def test_paystack_reference_names_its_folio(self):
		self.assertEqual(self.find("Hotel A", "Paystack", "FOLIO-2026-00012-a1b2c3d4"), "FOLIO-2026-00012")

	def test_narration_with_booking_number(self):
		self.assertEqual(self.find("Hotel A", "Bank Transfer", "TRF881", "pymt for res-2026-00007 thanks"),
		                 "FOLIO-2026-00012")

	def test_other_propertys_folio_is_not_matched(self):
		self.assertIsNone(self.find("Hotel A", "Bank Transfer", "TRF9", "FOLIO-2026-00099"))

	def test_nothing_to_go_on(self):
		self.assertIsNone(self.find("Hotel A", "Bank Transfer", "TRF10", "school fees"))


class TestPaystackMismatch(unittest.TestCase):
	def mismatch(self, ref, cur):
		with patch("kamra.payments._currency", return_value=("NGN", "₦")):
			return paystack.mismatch("FOLIO-2026-00012", "Hotel A", ref, cur)

	def test_issued_reference_in_naira_is_fine(self):
		self.assertIsNone(self.mismatch("FOLIO-2026-00012-a1b2c3d4", "NGN"))

	def test_wrong_currency_is_parked(self):
		self.assertIn("USD", self.mismatch("FOLIO-2026-00012-a1b2c3d4", "USD"))

	def test_reference_of_another_folio_is_parked(self):
		self.assertIn("not issued", self.mismatch("FOLIO-2026-00099-a1b2c3d4", "NGN"))
