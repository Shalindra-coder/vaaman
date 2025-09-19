# Copyright (c) 2025, Pratul Tiwari and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Material Request", "fieldname": "material_request", "fieldtype": "Link", "options": "Material Request", "width": 150},
        {"label": "MR Date", "fieldname": "mr_date", "fieldtype": "Date", "width": 100},

        {"label": "Purchase Order", "fieldname": "purchase_order", "fieldtype": "Link", "options": "Purchase Order", "width": 150},
        {"label": "PO Date", "fieldname": "po_date", "fieldtype": "Date", "width": 100},
        {"label": "Supplier", "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 180},
        {"label": "PO Grand Total", "fieldname": "po_grand_total", "fieldtype": "Currency", "width": 150},
        {"label": "Cost Center", "fieldname": "cost_center", "fieldtype": "Link","options":"Cost Center", "width": 150},

        {"label": "Purchase Receipt", "fieldname": "purchase_receipt", "fieldtype": "Link", "options": "Purchase Receipt", "width": 150},
        {"label": "GRN Date", "fieldname": "grn_date", "fieldtype": "Date", "width": 100},
        {"label": "PR Grand Total", "fieldname": "pr_grand_total", "fieldtype": "Currency", "width": 150},
        {"label": "Supplier Delivery Note", "fieldname": "supplier_delivery_note", "fieldtype": "Data", "width": 150},

        {"label": "Purchase Invoice", "fieldname": "purchase_invoice", "fieldtype": "Link", "options": "Purchase Invoice", "width": 150},
        {"label": "PI Date", "fieldname": "pi_date", "fieldtype": "Date", "width": 100},
        {"label": "Supplier Invoice No", "fieldname": "bill_no", "fieldtype": "Data", "width": 150},
        {"label": "Supplier Invoice Date", "fieldname": "bill_date", "fieldtype": "Date", "width": 150},
        {"label": "PI Grand Total", "fieldname": "pi_grand_total", "fieldtype": "Currency", "width": 150},

        {"label": "Payment Request", "fieldname": "payment_request", "fieldtype": "Link", "options": "Payment Request", "width": 150},
        {"label": "Amount", "fieldname": "payment_amount", "fieldtype": "Currency", "width": 150},

        {"label": "Payment Entry", "fieldname": "payment_entry", "fieldtype": "Link", "options": "Payment Entry", "width": 150},
        {"label": "Reference No", "fieldname": "reference_no", "fieldtype": "Data", "width": 150},
        {"label": "Reference Date", "fieldname": "reference_date", "fieldtype": "Date", "width": 150},
    ]

def get_data(filters):
    conditions = ""
    if filters.get("from_date"):
        conditions += " AND mr.transaction_date >= %(from_date)s"
    if filters.get("to_date"):
        conditions += " AND mr.transaction_date <= %(to_date)s"
    if filters.get("supplier"):
        conditions += " AND po.supplier = %(supplier)s"
    query = f"""
        SELECT
            mr.name AS material_request,
            mr.transaction_date AS mr_date,

            po.name AS purchase_order,
            po.transaction_date AS po_date,
            po.supplier AS supplier,
            po.grand_total AS po_grand_total,
            po.cost_center AS cost_center,

            pr.name AS purchase_receipt,
            pr.posting_date AS grn_date,
            pr.grand_total AS pr_grand_total,
            pr.supplier_delivery_note AS supplier_delivery_note,

            pi.name AS purchase_invoice,
            pi.posting_date AS pi_date,
            pi.bill_no AS bill_no,
            pi.bill_date AS bill_date,
            pi.grand_total AS pi_grand_total,

            payreq.name AS payment_request,
            payreq.grand_total AS payment_amount,

            pe.name AS payment_entry,
            pe.reference_no AS reference_no,
            pe.reference_date AS reference_date

        FROM `tabMaterial Request` mr

        LEFT JOIN `tabPurchase Order Item` poi 
            ON poi.material_request = mr.name
        LEFT JOIN `tabPurchase Order` po 
            ON po.name = poi.parent AND po.docstatus = 1

        LEFT JOIN `tabPurchase Receipt Item` pri 
            ON pri.purchase_order = po.name
        LEFT JOIN `tabPurchase Receipt` pr 
            ON pr.name = pri.parent AND pr.docstatus = 1

        LEFT JOIN `tabPurchase Invoice Item` pii 
            ON pii.purchase_receipt = pr.name
        LEFT JOIN `tabPurchase Invoice` pi 
            ON pi.name = pii.parent AND pi.docstatus = 1

        LEFT JOIN `tabPayment Request` payreq
            ON payreq.reference_name = pi.name 
           AND payreq.reference_doctype = 'Purchase Invoice'
           AND payreq.docstatus = 1

        LEFT JOIN `tabPayment Entry Reference` per
            ON per.reference_name = pi.name 
           AND per.reference_doctype = 'Purchase Invoice'
        LEFT JOIN `tabPayment Entry` pe
            ON pe.name = per.parent AND pe.docstatus = 1

        WHERE mr.docstatus = 1 {conditions}
        ORDER BY mr.transaction_date, po.transaction_date, pr.posting_date, pi.posting_date, pe.posting_date
    """

    return frappe.db.sql(query, filters, as_dict=True)