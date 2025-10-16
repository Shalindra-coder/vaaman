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
import frappe
from frappe.utils import flt
from frappe.utils.file_manager import save_file

@frappe.whitelist()
def create_supplier_quotation(**kwargs):
    data = json.loads(kwargs.get("doc", "{}"))
    item_data = json.loads(kwargs.get("item_details", "[]"))
    payment_term_data = json.loads(kwargs.get("payment_term_data", "[]"))
    other_details = json.loads(kwargs.get("other_details", "{}"))

    sq = frappe.new_doc("Supplier Quotation")
    sq.supplier = data.get("supplier")
    sq.terms = data.get("terms")
    sq.company = data.get("company")
    sq.currency = data.get("currency")

    # Append items (let ERPNext compute totals)
    for value in item_data:
        sq.append(
            "items",
            {
                "item_code": value.get("item_code"),
                "qty": flt(value.get("qty", 0)),
                "discount_percentage": flt(value.get("custom_discount_", 0)),
                "warehouse": value.get("warehouse"),
                "rate": flt(value.get("rate", 0)),  # Unit rate
                "price_list_rate": flt(value.get("rate", 0)),  # Assuming input is price list rate
                "request_for_quotation": data.get("name"),
            },
        )

    # Get tax account head
    account_head = frappe.db.get_value(
        "Account",
        {
            "company": data.get("company"),
            "account_type": "Tax",
            "is_group": 0,
        },
        "name",
    )
    if not account_head:
        account_head = frappe.get_cached_value("Company", data.get("company"), "default_tax_account")
        if not account_head:
            frappe.throw("No valid tax account found for company")

    # freight_account = "Freight Charges - VD"

    freight_account = "Freight and Forwarding Charges - VEIL"
    # account_head = "GST Expense - VEIL"
    if not frappe.db.exists("Account", freight_account):
        frappe.throw(f"Freight account '{freight_account}' not found—create it as Expense type")

    gst_rate = flt(other_details.get("gstValue", 0))
    freight_rate = flt(other_details.get("freightValue", 0))

    # Append GST if >0 (on Net Total)
    if gst_rate > 0:
        sq.append(
            "taxes",
            {
                "charge_type": "On Net Total",
                "account_head":"GST Expense - VEIL",
                "rate": gst_rate,
                "description": "GST Rate",
            },
        )

    # Append freight only if >0 (independent, on Net Total)
    if freight_rate > 0:
        sq.append(
            "taxes",
            {
                "charge_type": "On Net Total",  # Or "On Previous Row Total" + "row_id": 1 for after GST
                "account_head": freight_account,
                "rate": freight_rate,
                "description": "Freight Charges",
            },
        )

    # Set custom fields
    sq.custom_gst_ = gst_rate
    sq.custom_freight_ = freight_rate

    # Incoterm
    encoterm = other_details.get("Encoterm")
    if encoterm and encoterm != "Incoterm":
        sq.incoterm = encoterm

    # Payment terms/schedule
    payment_template = other_details.get("payment_terms_template")
    if payment_template:
        sq.custom_payment_term_template = payment_template
        for terms in payment_term_data:
            sq.append(
                "custom_payment_schedule",
                {
                    "payment_term": terms.get("paymentTerm"),
                    "description": terms.get("description"),
                    "due_date": terms.get("dueDate"),
                    "invoice_portion": flt(terms.get("percentage", "").replace("%", "").strip()),
                    "payment_amount": flt(terms.get("amount", "").replace(",", "").strip()),
                },
            )

    # Auto-fill, save, and submit
    sq.run_method("set_missing_values")
    # sq.taxes_and_charges = "Manual"  # For custom taxes
    sq.save(ignore_permissions=True)
    sq.submit()

    # Attach file
    attach_file = other_details.get("attach_file")
    if attach_file and attach_file.get("content"):
        try:
            file_name = attach_file.get("file_name")
            file_content = base64.b64decode(attach_file.get("content"))
            save_file(file_name, file_content, sq.doctype, sq.name, is_private=1)
        except Exception as e:
            frappe.log_error(f"File attachment failed for SQ {sq.name}: {str(e)}")

    frappe.db.commit()
    return sq.name

@frappe.whitelist()
def get_payment_schedule(template_name):
	payment_term_template = frappe.db.get_all(
		"Payment Terms Template Detail", {"parent": template_name}, ["*"]
	)
	return payment_term_template