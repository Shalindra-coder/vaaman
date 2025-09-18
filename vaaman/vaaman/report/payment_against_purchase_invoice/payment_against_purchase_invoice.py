# Copyright (c) 2025, Pratul Tiwari and contributors
# For license information, please see license.txt

# import frappe


import frappe

def execute(filters=None):
    columns = [
        {"label": "Purchase Invoice", "fieldname": "purchase_invoice", "fieldtype": "Link", "options": "Purchase Invoice", "width": 200},
        {"label": "Payment Entry", "fieldname": "payment_entry", "fieldtype": "Link", "options": "Payment Entry", "width": 200},
        {"label": "Supplier", "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 150},
        {"label": "Account Paid From", "fieldname": "paid_from", "fieldtype": "Link", "options": "Account", "width": 150},
        {"label": "Account Paid To", "fieldname": "paid_to", "fieldtype": "Link", "options": "Account", "width": 150},
        {"label": "Paid Amount", "fieldname": "paid_amount", "fieldtype": "Currency", "width": 150},
        {"label": "Mode of Payment", "fieldname": "mode_of_payment", "fieldtype": "Data", "width": 150},
        {"label": "Reference No", "fieldname": "reference_no", "fieldtype": "Data", "width": 150},
        {"label": "Reference Date", "fieldname": "reference_date", "fieldtype": "Date", "width": 150},
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 150},
    ]

    conditions = ["pe.docstatus = 1"]
    values = {}

    if filters.get("supplier"):
        conditions.append("pi.supplier = %(supplier)s")
        values["supplier"] = filters.get("supplier")

    if filters.get("mode_of_payment"):
        conditions.append("pe.mode_of_payment = %(mode_of_payment)s")
        values["mode_of_payment"] = filters.get("mode_of_payment")
    
    if filters.get("purchase_invoice"):
        conditions.append("per.reference_name = %(purchase_invoice)s")
        values["purchase_invoice"] = filters.get("purchase_invoice")

    if filters.get("payment_entry"):
        conditions.append("pe.name = %(payment_entry)s")
        values["payment_entry"] = filters.get("payment_entry")

    sql_query = """
        SELECT
            per.reference_name AS purchase_invoice,
            pe.name AS payment_entry,
            pi.supplier AS supplier,
            pe.paid_from AS paid_from,
            pe.paid_to AS paid_to,
            pe.paid_amount AS paid_amount,
            pe.mode_of_payment AS mode_of_payment,
            pe.reference_no AS reference_no,
            pe.reference_date AS reference_date,
            pe.posting_date AS posting_date
        FROM `tabPayment Entry` pe
        JOIN `tabPayment Entry Reference` per 
            ON per.parent = pe.name AND per.reference_doctype = 'Purchase Invoice'
        JOIN `tabPurchase Invoice` pi 
            ON pi.name = per.reference_name
    """

    if conditions:
        sql_query += " WHERE " + " AND ".join(conditions)

    sql_query += " ORDER BY pe.posting_date DESC"

    data = frappe.db.sql(sql_query, values, as_dict=True)

    return columns, data

