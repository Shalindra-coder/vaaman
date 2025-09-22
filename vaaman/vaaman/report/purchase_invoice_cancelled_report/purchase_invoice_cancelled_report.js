// Copyright (c) 2025, Pratul Tiwari and contributors
// For license information, please see license.txt


frappe.query_reports["Purchase Invoice Cancelled Report"] = {
	"filters": [
{
      "fieldname": "from_date",
      "label": "From Date",
      "fieldtype": "Date"
    },
    {
      "fieldname": "to_date",
      "label": "To Date",
      "fieldtype": "Date"
    },
    {
      "fieldname": "user",
      "label": "User",
      "fieldtype": "Link",
      "options": "User"
    }
	],
	onload: function(report) {
        report.set_filter_value("from_date", null);
        report.set_filter_value("to_date", null);
	}
};
