#Copyright (c) 2025, Pratul Tiwari and contributors
#For license information, please see license.txt

import frappe
from collections import defaultdict

def execute(filters=None):

    columns = [
        {"label": "Purchase Invoice","fieldname": "purchase_invoice", "fieldtype": "Link", "options": "Purchase Invoice", "width": 200 },
        {"label": "Approved By","fieldname": "approved_by","fieldtype": "Data", "width": 180 },
        {"label": "Full Name","fieldname": "full_name","fieldtype": "Data", "width": 150},
        {"label": "Approved On","fieldname": "approved_on","fieldtype": "Date","width": 120 },
    ]

    sql_query = """
        SELECT
            c.reference_name AS purchase_invoice,
            c.owner AS approved_by,
            c.creation AS approved_on,
            pi.supplier AS supplier,
            pi.grand_total AS total_amount
        FROM
            `tabComment` c
        JOIN
            `tabPurchase Invoice` pi
            ON pi.name = c.reference_name
        WHERE
            c.reference_doctype = 'Purchase Invoice'
            AND LOWER(TRIM(c.content)) = 'approved'
    """

    conditions = []
    values = {}

    if filters:
        if filters.get("from_date"):
            conditions.append("DATE(c.creation) >= %(from_date)s")
            values["from_date"] = filters["from_date"]

        if filters.get("to_date"):
            conditions.append("c.creation <= DATE_ADD(%(to_date)s, INTERVAL 1 DAY)")
            values["to_date"] = filters["to_date"]

        if filters.get("user"):
            conditions.append("c.owner = %(user)s")
            values["user"] = filters["user"]

    if conditions:
        sql_query += " AND " + " AND ".join(conditions)
    sql_query += " ORDER BY c.creation DESC"
    data = frappe.db.sql( sql_query, values, as_dict=True)


 # added  user Full name 
    for row in data:
        row["full_name"] = frappe.db.get_value(
            "User", row["approved_by"], "full_name"
        )

# USER-WISE INVOICE COUNT
    user_invoice_count = defaultdict(int)

    for row in data:
        user_invoice_count[row["full_name"]] += 1

 # BAR CHART       
    chart = {
    "data": {
        "labels": list(user_invoice_count.keys()),   
        "datasets": [
            {
                "name": "Approved Invoice Count",
                "values": list(user_invoice_count.values())
            }
        ]
    },
    "type": "bar",
    "height": 500,
    
}

    return columns, data, None, chart

