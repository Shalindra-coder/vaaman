# Copyright (c) 2026, Pratul Tiwari and contributors
# For license information, please see license.txt


import frappe

def execute(filters=None):
    if not filters: filters = {}
    vendors = get_vendors(filters)
    columns = get_columns(vendors)
    data = get_data(filters, vendors)
    return columns, data


# ================= COLUMNS =================
def get_columns(vendors):
    columns = [
        {"label": "S. No", "fieldname": "s_no", "fieldtype": "Int", "width": 60},
        {"label": "Item Description", "fieldname": "item_description", "fieldtype": "Data", "width": 200},
        {"label": "QTY", "fieldname": "qty", "fieldtype": "Float", "width": 80},
        {"label": "UOM", "fieldname": "uom", "fieldtype": "Data", "width": 80},
        {"label": "HSN", "fieldname": "hsn", "fieldtype": "Data", "width": 80},
        {"label": "GST %", "fieldname": "gst", "fieldtype": "Float", "width": 70},
        {"label": "LPP Rate", "fieldname": "lpp_rate", "fieldtype": "Currency", "width": 100},
    ]

    for v in vendors:
        key = frappe.scrub(v)
        columns.extend([
            {"label": "Initial", "fieldname": f"{key}_initial", "fieldtype": "Currency", "width": 110, "supplier_name": v},
            {"label": "Negotiated", "fieldname": f"{key}_negotiated", "fieldtype": "Currency", "width": 120, "supplier_name": v},
            {"label": "Total", "fieldname": f"{key}_total", "fieldtype": "Currency", "width": 120, "supplier_name": v},
            {"label": f"{v} Payment Terms", "fieldname": f"{key}_payment_terms", "fieldtype": "Data", "width": 150},
            {"label": f"{v} Incoterms", "fieldname": f"{key}_incoterms", "fieldtype": "Data", "width": 150},
           
        ])

    columns.extend([
        {"label": "L1 Initial", "fieldname": "l1_initial", "fieldtype": "Currency", "width": 110},
        {"label": "L1 Negotiated", "fieldname": "l1_negotiated", "fieldtype": "Currency", "width": 120},
        {"label": "Supplier", "fieldname": "l1_supplier", "fieldtype": "Data", "width": 110},
    ])

    return columns


def get_vendors(filters):
    conds = {"docstatus": 1}
    
    if filters.get("rfq"): conds["request_for_quotation"] = filters.get("rfq")
    if filters.get("company"): conds["company"] = filters.get("company")
    if filters.get("supplier"): conds["supplier"] = filters.get("supplier")
    if filters.get("supplier_quotation"): conds["name"] = filters.get("supplier_quotation")
    
    # Dates
    if filters.get("from_date") and filters.get("to_date"):
        conds["transaction_date"] = ["between", [filters.get("from_date"), filters.get("to_date")]]

    vendors = frappe.get_all(
        "Supplier Quotation",
        filters=conds,
        fields=["supplier"],
        distinct=True
    )
    return [v.supplier for v in vendors]

def get_hsn(item_code):
    return frappe.db.get_value("Item", item_code, "gst_hsn_code") or ""


def get_gst_from_item_template(template_name):
    if not template_name:
        return 0

    template = frappe.get_doc("Item Tax Template", template_name)
    rates = [row.tax_rate for row in template.taxes if row.tax_rate]
    return max(rates) if rates else 0


def get_lpp_rate(item_code):
    return frappe.db.get_value(
        "Purchase Invoice Item",
        {"item_code": item_code, "docstatus": 1},
        "rate",
        order_by="creation desc"
    ) or 0


def get_freight_amount(sq_name):
    taxes = frappe.get_all(
        "Purchase Taxes and Charges",
        filters={
            "parent": sq_name,
            "account_head": ["like", "%Freight%"]
        },
        fields=["tax_amount"]
    )

    total = 0
    for t in taxes:
        total += t.tax_amount or 0

    return round(total,2)

def get_data(filters, vendors):
    # Filters variable se value nikalna
    rfq = filters.get("rfq")
    sq_filter = filters.get("supplier_quotation")
    item_filter = filters.get("item_code")

    sq_conds = {"docstatus": 1}
    if rfq: sq_conds["request_for_quotation"] = rfq
    if sq_filter: sq_conds["name"] = sq_filter 
    if filters.get("company"): sq_conds["company"] = filters.get("company")
    
    quotations = frappe.get_all(
        "Supplier Quotation",
        filters=sq_conds,
        fields=["name", "supplier", "creation"],
        order_by="supplier, creation"
    )
    
    
    supplier_map = {}
    for q in quotations:
        supplier_map.setdefault(q.supplier, []).append(q)

    item_map = {}
    s_no = 1

    # -------- ITEM DATA --------
    for supplier, quotes in supplier_map.items():
        supplier_key = frappe.scrub(supplier)

        first_q = quotes[0]
        last_q = quotes[-1]
        
        
        item_conds = {"parent": first_q.name}
        if item_filter:
            item_conds["item_code"] = item_filter
        first_items = frappe.get_all(
            "Supplier Quotation Item",
           
            filters=item_conds,
            fields=["item_code", "item_name", "qty", "uom", "rate", "item_tax_template"]
        )
        
        
        last_item_conds = {"parent": last_q.name}
        if item_filter:
            last_item_conds["item_code"] = item_filter
        
        
        last_items = frappe.get_all(
            "Supplier Quotation Item",
           
            filters=last_item_conds,
            fields=["item_code", "rate"]
        )

        last_rate_map = {i.item_code: i.rate for i in last_items}

        for it in first_items:
            if it.item_code not in item_map:
                item_map[it.item_code] = {
                    "s_no": s_no,
                    "item_description": it.item_name,
                    "qty": it.qty,
                    "uom": it.uom,
                    "hsn": get_hsn(it.item_code),
                    "gst": get_gst_from_item_template(it.item_tax_template),
                    "lpp_rate": get_lpp_rate(it.item_code),
                }
                s_no += 1

            qty = it.qty or 0
            negotiated = last_rate_map.get(it.item_code) or 0

            item_map[it.item_code][f"{supplier_key}_initial"] = it.rate
            item_map[it.item_code][f"{supplier_key}_negotiated"] = negotiated
            item_map[it.item_code][f"{supplier_key}_total"] = negotiated * qty

    # -------- L1 --------
    for item in item_map.values():
        lowest = None
        lowest_supplier = None

        for v in vendors:
            key = frappe.scrub(v)
            rate = item.get(f"{key}_negotiated")
            if rate is not None:
                if lowest is None or rate < lowest["rate"]:
                    lowest = {"rate": rate, "initial": item.get(f"{key}_initial")}
                    lowest_supplier = v

        if lowest:
            item["l1_initial"] = lowest["initial"]
            item["l1_negotiated"] = lowest["rate"]
            item["l1_supplier"] = lowest_supplier

    data_list = list(item_map.values())
    if not data_list:
        return []
    
    
    # -------- SUMMARY ROWS --------
    basic_row = {"item_description": "Basic Total", "is_summary": 1}
    freight_row = {"item_description": "Freight & Forwarding", "is_summary": 1}
    no_gst_row = {"item_description": "Grand Total Without GST", "is_summary": 1}
    gst_row = {"item_description": "GST Total", "is_summary": 1}
    final_row = {"item_description": "Grand Total With GST", "is_summary": 1}
    
    payment_terms_row = {"item_description": "Payment Terms", "is_summary": 1}
    incoterms_row = {"item_description": "IncoTerms", "is_summary": 1}
    ranking_row = {"item_description": "Supplier Ranking on total with GST", "is_summary": 1}
    for v in vendors:
        key = frappe.scrub(v)

        basic_sum = 0
        gst_sum = 0

        sq_name = supplier_map[v][-1].name
        # get last quotation document
        sq_doc = frappe.get_doc("Supplier Quotation", sq_name)
       
       
        payment_terms_row[f"{key}_payment_terms"] = (
            sq_doc.get("custom_payment_term_template")
            or "Not Set"
        )
        
        incoterms_row[f"{key}_incoterms"] = sq_doc.get("incoterm") or ""
        
    
        for item in data_list:
            qty = item.get("qty") or 0
            rate = item.get(f"{key}_negotiated") or 0
            gst_percent = item.get("gst") or 0

            line_total = qty * rate
            basic_sum += line_total
            gst_sum += round(line_total * gst_percent / 100, 2)

        freight_amount = get_freight_amount(sq_name)
        no_gst_total = round(basic_sum + freight_amount, 2)
        final_total = round(no_gst_total + gst_sum, 2)

        basic_row[f"{key}_total"] = round(basic_sum, 2)
        freight_row[f"{key}_total"] = freight_amount
        no_gst_row[f"{key}_total"] =(no_gst_total)
        gst_row[f"{key}_total"] = round(gst_sum, 2)
        final_row[f"{key}_total"] = final_total
   
    # -------- SUPPLIER RANKING --------
    supplier_totals = {}

    for v in vendors:
        key = frappe.scrub(v)
     
        total = final_row.get(f"{key}_total")
        
        supplier_totals[v] = total
    sorted_suppliers = sorted(supplier_totals.items(), key=lambda x: x[1])

    rank = 1
    for supplier, total in sorted_suppliers:
        key = frappe.scrub(supplier)
        ranking_row[f"{key}_total"] = rank
        rank += 1

    data_list.extend([basic_row, freight_row, no_gst_row, gst_row, final_row,  payment_terms_row, incoterms_row, ranking_row])

    return data_list




