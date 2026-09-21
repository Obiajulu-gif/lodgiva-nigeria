"""Photos and copy for the sample "Lodgiva Demo Hotel".

Demo only: a real hotel uploads its own photos in Booking Settings. The
images ship inside this app (public/demo, credits in CREDITS.md) so a fresh
Oracle install shows a finished booking page without reaching the internet.

    bench --site <site> execute lodgiva_nigeria.demo.apply_demo_photos
"""

import frappe

PROPERTY = "Lodgiva Demo Hotel"
BASE = "/assets/lodgiva_nigeria/demo"

GALLERY = [
	("exterior", "The hotel, Ikeja GRA"),
	("lobby", "Reception, open 24 hours"),
	("pool", "The pool terrace"),
	("restaurant", "All-day dining"),
	("buffet", "Breakfast buffet, included on B&B rates"),
	("lounge", "Residents' lounge"),
]

ROOMS = {
	"STD": ("std-1", ["std-1", "std-2"], "Queen bed, rain shower, work desk and fast Wi-Fi."),
	"DLX": ("dlx-1", ["dlx-1", "dlx-2"], "King bed, garden view, lounge chair and minibar."),
	"EXS": ("exs-1", ["exs-1", "exs-2", "exs-3"], "Separate living room, king bed and a city view."),
}

DESCRIPTION = (
	"A calm, modern hotel in Ikeja GRA, ten minutes from the airport. "
	"24-hour power, fast Wi-Fi, a pool terrace and all-day dining - "
	"with rates in naira and VAT shown up front."
)


def _set_if_field(doc, fieldname, value):
	if doc.meta.has_field(fieldname):
		doc.set(fieldname, value)


@frappe.whitelist()
def apply_demo_photos(property: str = PROPERTY):
	frappe.only_for(("System Manager", "Administrator"))
	prop = frappe.get_doc("Property", property)
	prop.hero_image = f"{BASE}/hero-lagos.jpg"
	prop.og_image = f"{BASE}/hero-lagos.jpg"
	prop.set("gallery", [{"url": f"{BASE}/{f}.jpg", "caption": c} for f, c in GALLERY])
	for field in ("description", "about", "short_description", "tagline"):
		_set_if_field(prop, field, DESCRIPTION)
	prop.save(ignore_permissions=True)

	done = []
	for code, (cover, media, blurb) in ROOMS.items():
		name = frappe.db.get_value("Room Type", {"property": property, "room_type_code": code})
		if not name:
			continue
		rt = frappe.get_doc("Room Type", name)
		rt.image = f"{BASE}/{cover}.jpg"
		rt.set("media", [{"media_type": "Image", "url": f"{BASE}/{m}.jpg", "caption": ""} for m in media])
		for field in ("description", "short_description"):
			_set_if_field(rt, field, blurb)
		rt.save(ignore_permissions=True)
		done.append(code)

	frappe.db.commit()
	return {"property": property, "gallery": len(GALLERY), "room_types": done}
