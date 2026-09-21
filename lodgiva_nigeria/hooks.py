app_name = "lodgiva_nigeria"
app_title = "Lodgiva Nigeria"
app_publisher = "Domain-Plus International Ltd"
app_description = "Nigeria country pack, branding and integrations for Lodgiva PMS"
app_email = "engineering@lodgiva.com"
app_license = "agpl-3.0"

# Apps
# ------------------


# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "lodgiva_nigeria",
# 		"logo": "/assets/lodgiva_nigeria/logo.png",
# 		"title": "Lodgiva Nigeria",
# 		"route": "/lodgiva_nigeria",
# 		"has_permission": "lodgiva_nigeria.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/lodgiva_nigeria/css/lodgiva_nigeria.css"
# app_include_js = "/assets/lodgiva_nigeria/js/lodgiva_nigeria.js"

# include js, css files in header of web template
# web_include_css = "/assets/lodgiva_nigeria/css/lodgiva_nigeria.css"
# web_include_js = "/assets/lodgiva_nigeria/js/lodgiva_nigeria.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "lodgiva_nigeria/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "lodgiva_nigeria/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "lodgiva_nigeria.utils.jinja_methods",
# 	"filters": "lodgiva_nigeria.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "lodgiva_nigeria.install.before_install"
# after_install = "lodgiva_nigeria.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "lodgiva_nigeria.uninstall.before_uninstall"
# after_uninstall = "lodgiva_nigeria.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "lodgiva_nigeria.utils.before_app_install"
# after_app_install = "lodgiva_nigeria.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "lodgiva_nigeria.utils.before_app_uninstall"
# after_app_uninstall = "lodgiva_nigeria.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "lodgiva_nigeria.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "lodgiva_nigeria.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"lodgiva_nigeria.tasks.all"
# 	],
# 	"daily": [
# 		"lodgiva_nigeria.tasks.daily"
# 	],
# 	"hourly": [
# 		"lodgiva_nigeria.tasks.hourly"
# 	],
# 	"weekly": [
# 		"lodgiva_nigeria.tasks.weekly"
# 	],
# 	"monthly": [
# 		"lodgiva_nigeria.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "lodgiva_nigeria.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "lodgiva_nigeria.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "lodgiva_nigeria.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "lodgiva_nigeria.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["lodgiva_nigeria.utils.before_request"]
# after_request = ["lodgiva_nigeria.utils.after_request"]

# Job Events
# ----------
# before_job = ["lodgiva_nigeria.utils.before_job"]
# after_job = ["lodgiva_nigeria.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"lodgiva_nigeria.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []


# Lodgiva builds on Kamra: the Nigeria pack is claimed through Kamra's
# `kamra_localization` hook (merged across apps by frappe.get_hooks), so
# Nigeria works without editing the Kamra fork. Keep Lodgiva-specific
# behaviour here rather than in apps/kamra - that is what keeps upgrades
# from upstream Kamra a merge instead of a rewrite.
required_apps = ["kamra"]

kamra_localization = {
	"Nigeria": "lodgiva_nigeria.localization.nigeria",
}

# ── Lodgiva financial controls over Kamra ────────────────────────────────
# The vertical slice (gap matrix §8) found that Kamra let a guest depart
# owing money, let an unsettled folio be closed and invoiced, and accepted
# the same payment reference twice. These are enforced on the DOCUMENT, not
# only the REST route, so an internal caller cannot slip past them.
doc_events = {
	"Reservation": {
		"before_save": "lodgiva_nigeria.controls.reservation_before_save",
	},
	"Folio": {
		"before_save": "lodgiva_nigeria.controls.folio_before_save",
	},
}

# Nigerian schema defaults (currency, tenders, TIN labels) applied as
# Property Setters so Kamra's own doctypes stay untouched and upgradeable.
after_install = "lodgiva_nigeria.install.after_install"
after_migrate = "lodgiva_nigeria.install.after_migrate"
