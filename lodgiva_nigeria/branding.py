"""Lodgiva branding over Kamra's Frappe surfaces.

The Frappe desk login page, the app switcher and the browser tab take their
name and mark from hooks and Website Settings, so those can be rebranded from
this app - no Kamra edit, no merge conflict on upgrade. The React SPA's own
chrome is a build artefact and is rebranded in the fork instead.

AGPL note: rebranding the interface is permitted. Removing the licence notice
or the offer of source is not, so `source_link` stays in the navbar and the
booking page keeps its "built on Kamra (AGPL-3.0)" line with a source URL.
"""

import frappe

BRAND_NAME = "Lodgiva"
BRAND_TITLE = "Lodgiva PMS"
LOGO = "/assets/lodgiva_nigeria/lodgiva-mark.svg"
# AGPL §13: users interacting over a network must be offered the source.
SOURCE_URL = "https://github.com/Obiajulu-gif/lodgiva-pms"


def apply_branding():
	"""Idempotent; runs on install and on every migrate."""
	settings = frappe.get_single("Website Settings")
	settings.app_name = BRAND_TITLE
	settings.app_logo = LOGO
	settings.banner_image = LOGO
	settings.favicon = LOGO
	settings.brand_html = (
		f'<img src="{LOGO}" alt="{BRAND_NAME}" style="height:24px;vertical-align:middle">'
		f'<span style="margin-left:8px;font-weight:600">{BRAND_NAME}</span>'
	)
	settings.copyright = f"{BRAND_NAME} · Domain Plus International Limited"
	settings.footer_powered = (
		f'{BRAND_NAME} PMS · built on <a href="https://github.com/Kamra-PMS/kamra-pms">Kamra</a> '
		f'(AGPL-3.0) · <a href="{SOURCE_URL}">source</a>'
	)
	settings.flags.ignore_permissions = True
	settings.save(ignore_permissions=True)

	# The desk's own title bar and the login page heading.
	try:
		frappe.db.set_single_value("System Settings", "app_name", BRAND_TITLE)
	except Exception:
		pass  # older/newer Frappe may not carry the field; the hook still applies

	frappe.db.commit()
