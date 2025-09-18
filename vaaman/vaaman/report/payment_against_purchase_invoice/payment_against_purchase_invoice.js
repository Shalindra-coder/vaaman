// Copyright (c) 2025, Pratul Tiwari and contributors
// For license information, please see license.txt

frappe.query_reports["Payment Against Purchase Invoice"] = {
	"filters": [
        {
            "fieldname":"from_date",
            "label": "From Date",
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1) // last 1 month
        },
        {
            "fieldname":"to_date",
            "label": "To Date",
            "fieldtype": "Date",
            "default": frappe.datetime.get_today()
        },
        {
            "fieldname":"supplier",
            "label": "Supplier",
            "fieldtype": "Link",
            "options": "Supplier"
        },
        {
            "fieldname":"mode_of_payment",
            "label": "Mode of Payment",
            "fieldtype": "Link",
            "options": "Mode of Payment"
        },
        {
            "fieldname":"purchase_invoice",
            "label": "Purchase Invoice",
            "fieldtype": "Link",
            "options": "Purchase Invoice"
        },
        {
            "fieldname":"payment_entry",
            "label": "Payment Entry",
            "fieldtype": "Link",
            "options": "Payment Entry"
        }
	]
};
