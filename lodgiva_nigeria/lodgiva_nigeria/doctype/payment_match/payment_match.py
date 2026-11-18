from frappe.model.document import Document


class PaymentMatch(Document):
	def validate(self):
		self.reference = (self.reference or "").strip()
		self.match_key = f"{self.source}:{self.reference}"
