import frappe
from frappe.utils import flt, cint

@frappe.whitelist()
def update_status_db(docname):
    """
    Updates the custom_status of a single Payment Request based on its own amount and outstanding_amount.
    Returns the new status.
    """
    try:
        doc = frappe.get_doc("Payment Request", docname).reload()  # ensure latest data

        # Determine new status
        if doc.docstatus == 2:
            new_status = "Cancelled"
        elif not doc.custom_status or doc.workflow_state == "Draft":
            new_status = "Draft"
        elif doc.workflow_state == "Approval Pending By Management":
            new_status = "Ready to Pay"
        elif doc.docstatus == 1:
            new_status = get_payment_request_status(doc)
        else:
            new_status = "Draft"

        # Update if changed
        if doc.custom_status != new_status:
            frappe.db.set_value("Payment Request", docname, "custom_status", new_status)
            frappe.logger().info(f"Updated Payment Request {docname} custom_status to {new_status}")

        return new_status

    except Exception as e:
        frappe.log_error(f"update_status_db error for {docname}: {str(e)}", "Payment Request Sync Error")
        raise

def get_payment_request_status(doc):
    """
    Determines status using amount and outstanding_amount from the Payment Request itself.
    """
    try:
        amount = flt(doc.amount or 0)
        outstanding = flt(doc.outstanding_amount or 0)

        if amount == 0:
            return "Initiated"

        if outstanding == 0:
            return "Paid"
        elif 0 < outstanding < amount:
            return "Partially Paid"
        elif outstanding >= amount:
            return "Initiated"
        else:
            return "Initiated"
    except Exception as e:
        frappe.log_error(f"get_payment_request_status error for {doc.name}: {str(e)}", "Payment Request Sync Error")
        return "Initiated"

@frappe.whitelist()
def update_all_linked_payment_requests(doc, method=None):
    """
    On submission of a Payment Entry, update statuses of all linked Payment Requests.
    """
    try:
        references = doc.get("references", [])
        if not references or not isinstance(references, list):
            frappe.log_error(f"Invalid references in {doc.doctype} {doc.name}: {references}", "Payment Request Sync Error")
            return

        for ref in references:
            reference_doctype = ref.get("reference_doctype")
            reference_name = ref.get("reference_name")
            allocated_amount = flt(ref.get("allocated_amount", 0))

            if reference_doctype and reference_name and allocated_amount > 0:
                payment_requests = frappe.get_all(
                    "Payment Request",
                    filters={
                        "reference_doctype": reference_doctype,
                        "reference_name": reference_name,
                        "docstatus": 1
                    },
                    pluck="name"
                )

                for pr_name in payment_requests:
                    update_status_db(pr_name)

    except Exception as e:
        frappe.log_error(f"update_all_linked_payment_requests error in {doc.name}: {str(e)}", "Payment Request Sync Error")

def on_update(doc, method):
    """
    Sync ERPNext system status to custom_status (for Payment Request).
    """
    try:
        if doc.doctype == "Payment Request" and doc.custom_status != doc.status:
            doc.db_set("custom_status", doc.status)
            frappe.logger().info(f"Synced status to custom_status for {doc.name}")
    except Exception as e:
        frappe.log_error(f"on_update error for {doc.name}: {str(e)}", "Payment Request Sync Error")

from erpnext.accounts.doctype.payment_request.payment_request import update_payment_requests_as_per_pe_references as original_update

def custom_update_payment_requests(references, cancel=None):
    """
    Override ERPNext's update_payment_requests_as_per_pe_references to ensure correct handling of references.
    """
    try:
        if isinstance(references, frappe.model.Document) and references.doctype == "Payment Entry":
            references = references.get("references", [])
            frappe.log_error(f"Extracted references from Payment Entry {references.name}: {references}", "Payment Request Sync Debug")

        if not references or not isinstance(references, list):
            frappe.log_error(f"Invalid references in custom_update_payment_requests: {references}", "Payment Request Sync Error")
            return

        return original_update(references, cancel)

    except Exception as e:
        frappe.log_error(f"custom_update_payment_requests error: {str(e)}", "Payment Request Sync Error")
