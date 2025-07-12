import frappe
import json
from erpnext.accounts.doctype.unreconcile_payment.unreconcile_payment import (
    get_linked_payments_for_doc,
    create_unreconcile_doc_for_selection,
)

@frappe.whitelist()
def bulk_unreconcile_payment_entries(payment_entry_names):
    if isinstance(payment_entry_names, str):
        payment_entry_names = frappe.parse_json(payment_entry_names)

    success_count = 0
    failed_entries = []

    for pe in payment_entry_names:
        try:
            pe_doc = frappe.get_doc("Payment Entry", pe)

            # Get all linked docs (Purchase Invoice, Sales Invoice, Journal Entry)
            linked_payments = get_linked_payments_for_doc(
                company=pe_doc.company,
                doctype="Payment Entry",
                docname=pe,
            )

            if not linked_payments:
                failed_entries.append(f"No linked payments found for {pe}")
                continue

            # Build selections in the correct format
            selections = []
            for ref in linked_payments:
                selections.append({
                    "company": pe_doc.company,
                    "voucher_type": "Payment Entry",  # Correct: PE is the voucher
                    "voucher_no": pe,
                    "against_voucher_type": ref.get("voucher_type"),  # Purchase Invoice / Sales Invoice / Journal Entry
                    "against_voucher_no": ref.get("voucher_no"),
                    "allocated_amount": ref.get("allocated_amount"),
                    "account_currency": ref.get("account_currency"),
                })

            # Call the ERPNext built-in function
            create_unreconcile_doc_for_selection(selections=json.dumps(selections))

            success_count += 1

        except Exception as e:
            frappe.log_error(f"Failed to unreconcile {pe}: {e}")
            failed_entries.append(f"{pe}: {str(e)}")

    return {
        "status": "Completed",
        "unreconciled": success_count,
        "failed": failed_entries,
    }
