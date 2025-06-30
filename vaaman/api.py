import frappe
import json
from frappe.utils import nowdate, flt
from vaaman.utils import get_party_account_from_master
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
from erpnext.accounts.doctype.payment_request.payment_request import get_accounting_dimensions


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
            if not pr.mode_of_payment:
                raise Exception("Mode of Payment is required")

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
                    "Account",
                    {"account_type": "Bank", "company": pr.company, "is_group": 0},
                    "name"
                )
                if default_account:
                    pr.payment_account = default_account
                else:
                    raise Exception("Missing payment_account and no default bank account found")

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

            pe.update({
                "mode_of_payment": "NEFT",
                "reference_no": pr.name,
                "reference_date": nowdate(),
                "remarks": f"Payment Entry against {pr.reference_doctype} {pr.reference_name} via Payment Request {pr.name}",
                "cost_center": pr.get("cost_center"),
                "project": pr.get("project"),
                "paid_from": "",
                "paid_to": party_account if pr.payment_request_type == "Outward" else pr.payment_account,
                "party_type": party_type,
                "party": party,
            })

            # Optional: set default party bank account
            party_bank_account = frappe.db.get_value(
                "Bank Account",
                {"party_type": party_type, "party": party, "is_default": 1},
                "name"
            )
            if party_bank_account:
                pe.party_bank_account = party_bank_account

            # Currency setup
            pe.paid_from_account_currency = frappe.get_cached_value("Account", pe.paid_from, "account_currency")
            pe.paid_to_account_currency = frappe.get_cached_value("Account", pe.paid_to, "account_currency")

            if pe.paid_to_account_currency != pe.paid_from_account_currency:
                pe.source_exchange_rate = frappe.db.get_value(
                    "Currency Exchange",
                    {
                        "from_currency": pe.paid_to_account_currency,
                        "to_currency": pe.paid_from_account_currency
                    },
                    "exchange_rate"
                ) or 1.0

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
            if frappe.db.has_column("Payment Request", "custom_payment_entry"):
                pr.db_set("custom_payment_entry", pe.name)

            frappe.logger().info(f"[Bulk Payment Entry] Created: {pe.name} for {pr.name}")
            success.append(pe.name)

        except Exception as e:
            error_message = f"Failed to process {pr_name}: {str(e)}"
            frappe.logger().error(error_message)
            frappe.log_error(frappe.get_traceback(), f"[Bulk Payment Entry] Error for {pr_name}")
            failed.append({'name': pr_name, 'error': str(e)})

    return {
        'success': success,
        'failed': failed,
        'total': len(payment_requests),
        'success_count': len(success),
        'failed_count': len(failed)
    }
