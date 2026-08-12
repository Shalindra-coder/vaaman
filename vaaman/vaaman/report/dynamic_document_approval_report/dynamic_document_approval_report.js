// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt



frappe.query_reports["Dynamic Document Approval Report"] = {
    filters: [
        {
            fieldname: "doctype",
            label: __("DocType"),
            fieldtype: "Link",
            options: "DocType",
            reqd: 1
        },
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date"
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date"
        },
        {
            fieldname: "user",
            label: __("Approved By"),
            fieldtype: "Link",
            options: "User"
        }
    ],

    onload: function(report) {
        report.set_filter_value("from_date", null);
        report.set_filter_value("to_date", null);
    }
};