// Copyright (c) 2025, Pratul Tiwari and contributors
// For license information, please see license.txt

frappe.query_reports["Material To Payment Report"] = {
	"filters": [
         {
            "fieldname": "supplier",
            "label": __("Supplier"),
            "fieldtype": "Link",
            "options": "Supplier",
            "reqd": 0
        },
       {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date"

        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date"
        },
        {
            "fieldname": "cost_center",
            "label": __("Cost Center"),
            "fieldtype": "Link",
            "options": "Cost Center",
            "reqd": 0
        }

	],
	onload: function(report) {
        report.set_filter_value("from_date", null);
        report.set_filter_value("to_date", null);
	}
};
