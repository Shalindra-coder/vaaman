import frappe
import json
from frappe.utils import nowdate, flt
from vaaman.utils import get_party_account_from_master
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
from erpnext.accounts.doctype.payment_request.payment_request import get_accounting_dimensions

@frappe.whitelist()
def bulk_make_draft_payment_entries(payment_requests):
    if isinstance(payment_requests, str):
        payment_requests = json.loads(payment_requests)

    success, failed = [], []

    for pr_name in payment_requests:
        try:
            pr = frappe.get_doc("Payment Request", pr_name)
            if pr.docstatus != 1:
                raise Exception("Payment Request must be submitted")

            ref_doc = frappe.get_doc(pr.reference_doctype, pr.reference_name)

            # Determine party account
            if pr.reference_doctype in ["Sales Invoice", "POS Invoice"]:
                party_account = ref_doc.debit_to
            elif pr.reference_doctype == "Purchase Invoice":
                party_account = ref_doc.credit_to
            else:
                party_type = pr.party_type or "Customer"
                party = pr.party or ref_doc.get("customer")
                party_account = get_party_account_from_master(party_type, party, pr.company)

            party_account_currency = (
                pr.get("party_account_currency")
                or ref_doc.get("party_account_currency")
                or frappe.get_cached_value("Account", party_account, "account_currency")
            )

            party_amount = bank_amount = pr.outstanding_amount

            if party_account_currency == ref_doc.company_currency and party_account_currency != pr.currency:
                exchange_rate = ref_doc.get("conversion_rate")
                bank_amount = flt(pr.outstanding_amount / exchange_rate, pr.precision("grand_total"))

            pe = get_payment_entry(
                pr.reference_doctype,
                pr.reference_name,
                party_amount=party_amount,
                bank_account=pr.payment_account,
                bank_amount=bank_amount,
                created_from_payment_request=True,
            )

            pe.update({
                "mode_of_payment": pr.mode_of_payment,
                "reference_no": pr.name,
                "reference_date": nowdate(),
                "remarks": f"Payment Entry against {pr.reference_doctype} {pr.reference_name} via Payment Request {pr.name}",
                "cost_center": pr.get("cost_center"),
                "project": pr.get("project"),
            })

            if pr.currency != ref_doc.company_currency:
                if (
                    pr.payment_request_type == "Outward"
                    and pe.paid_from_account_currency == ref_doc.company_currency
                    and pe.paid_from_account_currency != pe.paid_to_account_currency
                ):
                    pe.paid_amount = pe.base_paid_amount = (
                        pe.target_exchange_rate * pe.received_amount
                    )

            for dim in get_accounting_dimensions():
                pe.set(dim, pr.get(dim))

            pe.insert(ignore_permissions=True)  # Draft only, no submit
            success.append(pe.name)

        except Exception as e:
            failed.append({'name': pr_name, 'error': str(e)})

    return {'success': success, 'failed': failed}
