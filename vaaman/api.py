import base64
import json



import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
from erpnext.accounts.doctype.payment_request.payment_request import get_accounting_dimensions
from frappe.utils import flt, nowdate
from frappe.utils.file_manager import save_file

from vaaman.utils import get_party_account_from_master


@frappe.whitelist()
def bulk_make_draft_payment_entries(payment_requests):
	if isinstance(payment_requests, str):
		try:
			payment_requests = json.loads(payment_requests)
		except Exception:
			frappe.throw("Invalid JSON input for payment_requests")

	if not payment_requests:
		frappe.throw("No Payment Requests provided")

	frappe.logger().info(f"[Bulk Payment Entry] Starting creation for: {payment_requests}")

	success, failed = [], []

	for pr_name in payment_requests:
		try:
			pr = frappe.get_doc("Payment Request", pr_name)

			# Basic validations
			if pr.docstatus != 1:
				raise Exception("Payment Request must be submitted")
			if pr.status == "Paid":
				raise Exception("Payment Request is already marked as Paid")
			if not flt(pr.outstanding_amount):
				raise Exception("Outstanding amount is zero")

			# Avoid duplicate PE creation
			existing_pe = frappe.db.exists("Payment Entry", {"reference_no": pr.name, "docstatus": ("<", 2)})
			if existing_pe:
				raise Exception(f"Already linked to Payment Entry {existing_pe}")

			ref_doc = frappe.get_doc(pr.reference_doctype, pr.reference_name)

			# Determine party & account
			if pr.reference_doctype in ["Sales Invoice", "POS Invoice"]:
				party_account = ref_doc.debit_to
				party_type = "Customer"
				party = ref_doc.get("customer")
			elif pr.reference_doctype == "Purchase Invoice":
				party_account = ref_doc.credit_to
				party_type = "Supplier"
				party = ref_doc.get("supplier")
			else:
				party_type = pr.party_type or "Customer"
				party = pr.party or ref_doc.get("customer") or ref_doc.get("supplier")
				if not party:
					raise Exception("Party not found on Payment Request or reference document")
				party_account = get_party_account_from_master(party_type, party, pr.company)

			# Fallback to default bank account for outward payments
			if not pr.payment_account and pr.payment_request_type == "Outward":
				default_account = frappe.db.get_value(
					"Account", {"account_type": "Bank", "company": pr.company, "is_group": 0}, "name"
				)
				if default_account:
					pr.payment_account = default_account
				else:
					raise Exception("Missing payment_account and no default bank account found")

			# Resolve party bank account
			bank_account = pr.get("bank_account")
			if not bank_account:
				bank_account = frappe.db.get_value(
					"Bank Account", {"party_type": party_type, "party": party, "is_default": 1}, "name"
				)

			# Currency logic
			party_account_currency = (
				pr.get("party_account_currency")
				or ref_doc.get("party_account_currency")
				or frappe.get_cached_value("Account", party_account, "account_currency")
			)

			party_amount = bank_amount = pr.outstanding_amount

			if party_account_currency == ref_doc.company_currency and party_account_currency != pr.currency:
				exchange_rate = ref_doc.get("conversion_rate")
				bank_amount = flt(pr.outstanding_amount / exchange_rate, pr.precision("grand_total"))

			# Create Payment Entry
			pe = get_payment_entry(
				pr.reference_doctype,
				pr.reference_name,
				party_amount=party_amount,
				bank_account=pr.payment_account,
				bank_amount=bank_amount,
				created_from_payment_request=True,
			)

			pe.update(
				{
					"mode_of_payment": "NEFT",
					"reference_no": "",
					"reference_date": "",
					"remarks": f"Payment Entry against {pr.reference_doctype} {pr.reference_name} via Payment Request {pr.name}",
					"cost_center": pr.get("cost_center"),
					"project": pr.get("project"),
					"paid_from": "",
					"paid_to": party_account if pr.payment_request_type == "Outward" else pr.payment_account,
					"party_type": party_type,
					"party": party,
					"party_bank_account": bank_account or "",
					"custom_party_bank_account_no": pr.get("bank_account_no") or "",
					"custom_party_bank_ifsc": pr.get("branch_code") or "",
					"custom_party_bank_name": pr.get("bank") or "",
				}
			)

			# Currency setup
			pe.paid_from_account_currency = frappe.get_cached_value(
				"Account", pe.paid_from, "account_currency"
			)
			pe.paid_to_account_currency = frappe.get_cached_value("Account", pe.paid_to, "account_currency")

			if pe.paid_to_account_currency != pe.paid_from_account_currency:
				pe.source_exchange_rate = (
					frappe.db.get_value(
						"Currency Exchange",
						{
							"from_currency": pe.paid_to_account_currency,
							"to_currency": pe.paid_from_account_currency,
						},
						"exchange_rate",
					)
					or 1.0
				)

			# Dimensions
			for dim in get_accounting_dimensions():
				pe.set(dim, pr.get(dim))

			for ref in pe.references:
				if ref.reference_doctype == pr.reference_doctype and ref.reference_name == pr.reference_name:
					ref.allocated_amount = flt(party_amount)
					ref.outstanding_amount = ref_doc.get("outstanding_amount")
					ref.payment_request = pr.name
					ref.total_amount = (
						ref_doc.get("grand_total")
						or ref_doc.get("base_grand_total")
						or ref_doc.get("rounded_total")
						or ref_doc.get("total")
					)

			# Optional: traceability comment
			pe.add_comment("Comment", text=f"Created via bulk tool from Payment Request {pr.name}")

			# Insert as draft
			pe.flags.ignore_mandatory = True
			pe.insert(ignore_permissions=True)

			# Optionally set a link back on PR (if custom field exists)
			if frappe.db.has_column("Payment Request", "custom_payment_initiated"):
				pr.db_set("custom_payment_initiated", 1)

			frappe.logger().info(f"[Bulk Payment Entry] Created: {pe.name} for {pr.name}")
			success.append(pe.name)

		except Exception as e:
			error_message = f"Failed to process {pr_name}: {e!s}"
			frappe.logger().error(error_message)
			frappe.log_error(frappe.get_traceback(), f"[Bulk Payment Entry] Error for {pr_name}")
			failed.append({"name": pr_name, "error": str(e)})

	return {
		"success": success,
		"failed": failed,
		"total": len(payment_requests),
		"success_count": len(success),
		"failed_count": len(failed),
	}







import base64
import json
import re
import frappe
from frappe.utils import flt
from frappe.utils.file_manager import save_file


@frappe.whitelist()
def create_supplier_quotation(**kwargs):

    # Data Parsing
    data = json.loads(kwargs.get("doc", "{}"))
    item_data = json.loads(kwargs.get("item_details", "[]"))
    payment_term_data = json.loads(kwargs.get("payment_term_data", "[]"))
    other_details = json.loads(kwargs.get("other_details", "{}"))

    # Initialize Supplier Quotation
    sq = frappe.new_doc("Supplier Quotation")
    sq.supplier = data.get("supplier")
    sq.terms = data.get("terms")
    sq.company = data.get("company")
    sq.currency = data.get("currency")
    sq.transaction_date = frappe.utils.nowdate()
    sq.buying_price_list = data.get("buying_price_list") or "Standard Buying"
    sq.status = "Draft"

    # Helper: Extract GST % from Template Name
    def get_gst_percentage(template_name):
        if not template_name:
            return 0.0
        match = re.search(r"(\d+(\.\d+)?)", str(template_name))
        return flt(match.group(1)) if match else 0.0

    total_net_amount_exclusive = 0.0
    total_gst_amount = 0.0

    # ITEM CALCULATION
    for item in item_data:

        qty = flt(item.get("qty", 0))
        rate = flt(item.get("rate", 0))  # Rate already discounted
        discount_p = flt(item.get("custom_discount_", 0))

        gst_template = item.get("custom_gst_percent") or item.get("item_tax_template")
        gst_p = get_gst_percentage(gst_template)

        # Rate discounted hai, isliye direct rate ko net_rate mana gaya hai
        net_rate = rate 
        
        # Row Net Amount (Qty * Net Rate)
        row_net_amount = qty * net_rate

        row_gst_amount = (row_net_amount * gst_p) / 100
        
        total_net_amount_exclusive += row_net_amount
        total_gst_amount += row_gst_amount

        sq.append("items", {
            "item_code": item.get("item_code"),
            "qty": qty,
            "rate": rate, 
            "discount_percentage": discount_p,
            "net_rate": net_rate, 
            "amount": qty * rate, 
            "net_amount": row_net_amount, 
            "warehouse": item.get("warehouse"),
            "request_for_quotation": data.get("name"),
            "custom_gst_percent": gst_template,
            "item_tax_template": gst_template,
            "base_net_amount": row_net_amount
        })

    # --- FIX START: FREIGHT CALCULATION ON NET TOTAL ONLY ---
    freight_p = flt(other_details.get("freight_percentage", 0))
    # Freight calculate ho raha hai sirf total_net_amount_exclusive par (Bina GST ke)
    freight_amount = (total_net_amount_exclusive * freight_p) / 100

    grand_total = total_net_amount_exclusive + total_gst_amount + freight_amount
    # --- FIX END ---

    # HEADER TOTALS
    sq.net_total = total_net_amount_exclusive
    sq.total_taxes_and_charges = total_gst_amount + freight_amount
    sq.grand_total = grand_total
    sq.base_grand_total = grand_total
    sq.custom_freight_ = freight_p

    # TAX TABLE
    if total_gst_amount > 0:
        sq.append("taxes", {
            "charge_type": "On Net Total",
            "account_head": "Input Tax IGST - VEIL",
            "tax_amount": total_gst_amount,
            "description": "Total GST Included in Items",
            "category": "Total"
        })

    if freight_amount > 0:
        sq.append("taxes", {
            "charge_type": "On Net Total",
            "account_head": "Freight and Forwarding Charges - PP",
            "tax_amount": freight_amount,
            "description": f"Freight Charges @ {freight_p}%",
            "category": "Total"
        })

    # PAYMENT TERMS
    payment_template = other_details.get("payment_terms_template")

    if payment_template:
        sq.custom_payment_term_template = payment_template

        for term in payment_term_data:
            portion = flt(str(term.get("percentage", "0")).replace("%", "").strip())
            amt = flt(str(term.get("amount", "0")).replace(",", "").strip())

            sq.append("custom_payment_schedule", {
                "payment_term": term.get("paymentTerm"),
                "description": term.get("description"),
                "due_date": term.get("dueDate"),
                "invoice_portion": portion,
                "payment_amount": amt
            })

    # INCOTERM
    incoterm = other_details.get("incoterm") or other_details.get("Encoterm")

    if incoterm and incoterm != "Incoterm":
        sq.incoterm = incoterm

    # SAVE DOCUMENT
    sq.flags.ignore_validate = True
    sq.run_method("set_missing_values")
    sq.insert(ignore_permissions=True)
    sq.status = "Draft"

    # FILE ATTACHMENT
    attach_file = other_details.get("attach_file")

    if attach_file and isinstance(attach_file, dict) and attach_file.get("content"):
        try:
            file_name = attach_file.get("file_name")
            file_content = base64.b64decode(attach_file.get("content"))
            save_file(file_name, file_content, sq.doctype, sq.name, is_private=1)
        except Exception as e:
            frappe.log_error(f"Attachment Error: {str(e)}")

    frappe.db.commit()

    return sq.name