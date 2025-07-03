import frappe
from frappe.utils import flt

@frappe.whitelist()
def update_status_db(docname=None, method=None):
    """
    Updates the custom_status of a single Payment Request based on its own amount and outstanding.
    Also fires a realtime event to update UI.
    """
    try:
        doc = frappe.get_doc("Payment Request", docname).reload()

        # Determine new status
        if doc.docstatus == 2:
            new_status = "Cancelled"
        elif not doc.custom_status or doc.workflow_state == "Draft":
            new_status = "Draft"
        elif doc.workflow_state == "Approval Pending By Management":
            new_status = "Ready to Pay"
        elif doc.docstatus == 1:
            new_status = get_payment_request_status(doc)
        elif doc.workflow_state == "Approved":
            new_status = "Initiated"
        else:
            new_status = "Draft"

        # Update only if changed
        if doc.custom_status != new_status:
            frappe.db.set_value("Payment Request", docname, "custom_status", new_status)
            frappe.logger().info(f"Updated Payment Request {docname} custom_status to {new_status}")

            # 🔔 Fire realtime event
            frappe.publish_realtime('payment_request_status_update', {
                'payment_request': docname,
                'new_status': new_status
            }, user='*')

        return new_status

    except Exception as e:
        frappe.log_error(f"update_status_db error for {docname}: {str(e)}", "Payment Request Sync Error")
        raise


def get_payment_request_status(doc):
    """
    Determines Payment Request status using its own grand_total and outstanding_amount.
    """
    try:
        amount = flt(doc.grand_total or 0)
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
    On submission or cancellation of a Payment Entry, update statuses of all linked Payment Requests.
    Runs updates in the background.
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
                    # Run in background
                    frappe.enqueue("vaaman.payment_request.update_status_db", docname=pr_name)

    except Exception as e:
        frappe.log_error(f"update_all_linked_payment_requests error in {doc.name}: {str(e)}", "Payment Request Sync Error")


# ➤ ERPNext core wrapper (keep if needed)
from erpnext.accounts.doctype.payment_request.payment_request import update_payment_requests_as_per_pe_references as original_update

def custom_update_payment_requests(references, cancel=None):
    """
    Override ERPNext's update_payment_requests_as_per_pe_references to ensure correct handling.
    """
    try:
        if isinstance(references, frappe.model.document.Document) and references.doctype == "Payment Entry":
            references = references.get("references", [])
            frappe.logger().info(f"Extracted references from Payment Entry: {references}")

        if not references or not isinstance(references, list):
            frappe.log_error(f"Invalid references in custom_update_payment_requests: {references}", "Payment Request Sync Error")
            return

        return original_update(references, cancel)

    except Exception as e:
        frappe.log_error(f"custom_update_payment_requests error: {str(e)}", "Payment Request Sync Error")


def sync_all_payment_requests():
    """
    Fallback sync - updates statuses for all submitted Payment Requests.
    """
    try:
        pr_names = frappe.get_all("Payment Request", filters={"docstatus": 1}, pluck="name")
        for name in pr_names:
            frappe.enqueue("vaaman.payment_request.update_status_db", docname=name)

    except Exception as e:
        frappe.log_error(f"sync_all_payment_requests error: {str(e)}", "Payment Request Sync Error")
