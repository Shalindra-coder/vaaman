app_name = "vaaman"
app_title = "Vaaman"
app_publisher = "Pratul Tiwari"
app_description = "For all the customization"
app_email = "ptpratul2@gmail.com"
app_license = "mit"

# Apps
# ------------------


# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "vaaman",
# 		"logo": "/assets/vaaman/logo.png",
# 		"title": "Vaaman",
# 		"route": "/vaaman",
# 		"has_permission": "vaaman.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/vaaman/css/vaaman.css"
# app_include_js = "/assets/vaaman/js/vaaman.js"

# include js, css files in header of web template
# web_include_css = "/assets/vaaman/css/vaaman.css"
# web_include_js = "/assets/vaaman/js/vaaman.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "vaaman/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}

app_include_js = ["/assets/vaaman/js/payment_request.js", "/assets/vaaman/js/reco.js"]

doctype_js = {
	"Payment Request": "public/js/payment_request.js",
	"Payment Entry": "public/js/reco.js",
}

doctype_list_js = {"Payment Request": "public/js/payment_request_list.js"}


# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "vaaman/public/icons.svg"

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

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "vaaman.utils.jinja_methods",
# 	"filters": "vaaman.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "vaaman.install.before_install"
# after_install = "vaaman.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "vaaman.uninstall.before_uninstall"
# after_uninstall = "vaaman.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "vaaman.utils.before_app_install"
# after_app_install = "vaaman.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "vaaman.utils.before_app_uninstall"
# after_app_uninstall = "vaaman.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "vaaman.notifications.get_notification_config"

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

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
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


doc_events = {
	"Payment Entry": {
		"on_submit": "vaaman.payment_request.update_all_linked_payment_requests",
		"on_cancel": "vaaman.payment_request.update_all_linked_payment_requests",
	},
	# Optional if you want auto status update on edit of Payment Request
	"Payment Request": {"on_update": "vaaman.payment_request.update_status_db"},
}


# Optional fallback to resync everything every 30 mins
scheduler_events = {"cron": {"* * * * *": ["vaaman.payment_request.sync_all_payment_requests"]}}


# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"vaaman.tasks.all"
# 	],
# 	"daily": [
# 		"vaaman.tasks.daily"
# 	],
# 	"hourly": [
# 		"vaaman.tasks.hourly"
# 	],
# 	"weekly": [
# 		"vaaman.tasks.weekly"
# 	],
# 	"monthly": [
# 		"vaaman.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "vaaman.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "vaaman.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "vaaman.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["vaaman.utils.before_request"]
# after_request = ["vaaman.utils.after_request"]

# Job Events
# ----------
# before_job = ["vaaman.utils.before_job"]
# after_job = ["vaaman.utils.after_job"]

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
# 	"vaaman.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }


fixtures = [
	{
		"dt": "Custom Field",
		"filters": [
			[
				"name",
				"in",
				[
					"Request for Quotation-custom_terms_and_conditions",
					"Supplier Quotation-custom_freight_",
					"Supplier Quotation-custom_gst_",
					"Supplier Quotation-custom_payment_schedule",
					"Supplier Quotation-custom_payment_term_template",
					"Supplier Quotation Item-custom_discount_amount_rfq",
					"Payment Request-workflow_state",
				],
			]
		],
	}
]
