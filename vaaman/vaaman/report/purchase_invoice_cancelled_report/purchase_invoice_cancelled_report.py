# Copyright (c) 2025, Pratul Tiwari and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns = [
        {"label": "Purchase Invoice", "fieldname": "purchase_invoice", "fieldtype": "Link", "options": "Purchase Invoice", "width": 200},
        {"label": "Cancelled By", "fieldname": "cancelled_by", "fieldtype": "Link", "options": "User", "width": 150},
        {"label": "Cancelled On", "fieldname": "cancelled_on", "fieldtype": "Date", "width": 120}
    ]

    sql_query = """
        SELECT
            c.reference_name as purchase_invoice,
            c.owner as cancelled_by,
            c.creation as cancelled_on
        FROM
            `tabComment` c
        WHERE
            c.reference_doctype = 'Purchase Invoice'
            AND LOWER(TRIM(c.content)) = 'cancelled'
    """
    
    conditions = []
    query_filters = {}

    if filters:
        if filters.get("from_date"):
            conditions.append("c.creation >= %(from_date)s")
            query_filters['from_date'] = filters.get('from_date')
        
        if filters.get("to_date"):
            conditions.append("c.creation <= %(to_date)s")
            query_filters['to_date'] = filters.get('to_date')
        
        if filters.get("user"):
            conditions.append("c.owner = %(user)s")
            query_filters['user'] = filters.get('user')
    
    if conditions:
        sql_query += " AND " + " AND ".join(conditions)

    sql_query += " ORDER BY c.creation DESC"

    data = frappe.db.sql(sql_query, query_filters, as_dict=1)

    return columns, data