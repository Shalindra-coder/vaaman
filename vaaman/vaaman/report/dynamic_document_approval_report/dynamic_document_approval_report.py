# Copyright (c) 2026, Pratul Tiwari and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):

    filters = filters or {}

    if not filters.get("doctype"):
        frappe.throw("Please select DocType")

    doctype = filters.get("doctype")

    # Check DocType exists
    if not frappe.db.exists("DocType", doctype):
        frappe.throw(f"DocType {doctype} does not exist")

    # Get actual table name
    table = frappe.qb.DocType(doctype)

    columns = [
        {
            "label": "Document",
            "fieldname": "document",
            "fieldtype": "Data",
            "width": 220
        },
        {
            "label": "Created On",
            "fieldname": "created_on",
            "fieldtype": "Datetime",
            "width": 160
        },
        {
            "label": "Approved By",
            "fieldname": "approved_by",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": "Full Name",
            "fieldname": "full_name",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": "Approved On",
            "fieldname": "approved_on",
            "fieldtype": "Datetime",
            "width": 160
        },
        {
            "label": "TAT Days",
            "fieldname": "tat_days",
            "fieldtype": "Float",
            "width": 100
        }
    ]

    # Dynamic table name
    table_name = "tab" + doctype

    query = f"""
        SELECT
            d.name AS document,
            d.creation AS created_on,
            c.owner AS approved_by,
            c.creation AS approved_on
        FROM
            `{table_name}` d
        INNER JOIN
            `tabComment` c
            ON c.reference_name = d.name
        WHERE
            c.reference_doctype = %(doctype)s
            AND LOWER(TRIM(c.content)) = 'approved'
    """

    values = {
        "doctype": doctype
    }

    conditions = []

    # From Date
    if filters.get("from_date"):
        conditions.append(
            "DATE(c.creation) >= %(from_date)s"
        )
        values["from_date"] = filters.get("from_date")

    # To Date
    if filters.get("to_date"):
        conditions.append(
            "DATE(c.creation) <= %(to_date)s"
        )
        values["to_date"] = filters.get("to_date")

    # User
    if filters.get("user"):
        conditions.append(
            "c.owner = %(user)s"
        )
        values["user"] = filters.get("user")

    if conditions:
        query += " AND " + " AND ".join(conditions)

    query += " ORDER BY c.creation DESC"

    data = frappe.db.sql(
        query,
        values,
        as_dict=True
    )

    # Full Name + TAT
    for row in data:

        row["full_name"] = frappe.db.get_value(
            "User",
            row["approved_by"],
            "full_name"
        ) or row["approved_by"]

        if row["created_on"] and row["approved_on"]:

            time_difference = (
                row["approved_on"] - row["created_on"]
            )

            row["tat_days"] = round(
                time_difference.total_seconds() / 86400,
                2
            )

        else:
            row["tat_days"] = 0

    return columns, data