# Lodgiva Nigeria

**The Nigerian half of [Lodgiva PMS](https://github.com/Obiajulu-gif/lodgiva-pms):
naira, VAT and TIN, Nigerian defaults, the money controls, and Lodgiva
branding.**

This is a Frappe app that installs next to `kamra` (the
[lodgiva-pms](https://github.com/Obiajulu-gif/lodgiva-pms) fork). It changes
Kamra's behaviour **from outside**, through hooks, document events and
Property Setters, so pulling an upstream Kamra release never conflicts with
it. Part of [Lodgiva](https://github.com/Obiajulu-gif/lodgiva).

## What it does

### Country pack: Nigeria

Kamra looks up a country pack for each property through its
`kamra_localization` hook. This app claims **Nigeria**:

| | Kamra's India default | With this app |
|---|---|---|
| Currency | ₹ INR | **₦ NGN**, locale `en-NG` |
| Tax | GST, split CGST/SGST, slabs by tariff | **VAT 7.5%**, one line, same rate at any tariff |
| Tax ID | GSTIN | **TIN** |
| Amount in words | "… Lakh … Only" | **"Naira … and … Kobo Only"** |
| Invoice footer | "…under the GST Act" | Service charge and state levies shown as separate lines, not VAT |

7.5% is a **configurable default, not tax advice**. A room type's own tax
percent overrides it. Confirm rates with a tax adviser before go-live.

### Money controls

A live test of Kamra found four ways money could go missing. This app
closes them on the **document**, not just the API route, so an internal
caller can't bypass them:

| Kamra allowed | Now |
|---|---|
| Checking out a guest who still owes money | Refused, naming the amount |
| Closing and invoicing a bill that isn't paid | Refused |
| The same bank-transfer reference posted twice | Refused as a duplicate |
| A naira payment stored as INR | Stored as NGN |

A hotel that bills companies after departure can switch on **Allow departure
with an unsettled balance** on the Property. The departure is then recorded
on the stay as a comment, never silently.

### Nigerian defaults

Applied as Property Setters on every `migrate`:

- Country Nigeria, currency NGN, time zone Africa/Lagos
- **POS Terminal** and **Bank Transfer** as tenders, each with a reference
- Guest nationality **Nigerian** and **NIN** as an ID type

### Branding

The Lodgiva name and logo on the Frappe login page, desk, favicon and app
launcher. After login, staff land on the app at `/lodgiva`.

### Demo hotel photos

`public/demo/` holds 14 photos for the sample "Lodgiva Demo Hotel", from
Unsplash under the free [Unsplash License](https://unsplash.com/license) and
credited in [`CREDITS.md`](lodgiva_nigeria/public/demo/CREDITS.md). To apply
them:

```bash
bench --site <site> execute lodgiva_nigeria.demo.apply_demo_photos
```

They're for demos only; a real hotel uploads its own photos in Booking
Settings.

## Install

The easiest route is the Lodgiva installer, which sets up everything on any
Ubuntu server: see
[`deploy/README.md`](https://github.com/Obiajulu-gif/lodgiva/blob/main/deploy/README.md).

Into an existing Frappe v16 bench that already has `payments` and
`lodgiva-pms`:

```bash
bench get-app https://github.com/Obiajulu-gif/lodgiva-nigeria --branch main
bench --site <site> install-app lodgiva_nigeria
bench --site <site> migrate
```

**Set the property's country to Nigeria.** That one field decides the tax
regime; a property with no country falls back to India.

## Tests

```bash
# Unit tests for the country pack; no site needed
env/bin/python -m unittest discover -s apps/lodgiva_nigeria -p "test_nigeria_pack.py" -v
```

`tests/test_controls_site.py` replays the four money defects against a
**disposable** site, and checks each is refused and that a settled stay
still checks out and invoices normally. It writes bookings, so never run it
against a site holding real data.

## Licence

AGPL-3.0, like Kamra, which this app extends.
