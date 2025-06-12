import frappe
from frappe.utils import flt, cint

@frappe.whitelist()
def update_status_db(docname):
    """
    Updates the custom_status of a single Payment Request based on workflow and reference document.
    Returns the new status.
    """
    try:
        doc = frappe.get_doc("Payment Request", docname)

        # Determine new status
        if doc.docstatus == 2:
            new_status = "Cancelled"
        elif not doc.custom_status or doc.workflow_state == "Draft":
            new_status = "Draft"
        elif doc.workflow_state == "Approval Pending By Management":
            new_status = "Ready to Pay"
        elif doc.docstatus == 1 and doc.reference_doctype and doc.reference_name:
            new_status = get_outstanding_status(doc.reference_doctype, doc.reference_name)
        else:
            new_status = "Initiated"

        # Only update if status has changed
        if doc.custom_status != new_status:
            frappe.db.set_value("Payment Request", docname, "custom_status", new_status)
            frappe.logger().info(f"Updated Payment Request {docname} custom_status to {new_status}")

        return new_status  # Return the new status for client-side use

    except Exception as e:
        frappe.log_error(f"update_status_db error for {docname}: {str(e)}", "Payment Request Sync Error")
        raise
@frappe.whitelist()
def get_outstanding_status(reference_doctype, reference_name):
    """
    Returns payment status like Paid, Partially Paid, or Initiated based on outstanding amount.
    """
    try:
        ref_doc = frappe.get_doc(reference_doctype, reference_name)

        if ref_doc.docstatus == 2:
            return "Cancelled"

        total = (
            flt(ref_doc.get("total", 0))
            or flt(ref_doc.get("base_grand_total", 0))
            or flt(ref_doc.get("rounded_total", 0))
        )
        outstanding = flt(ref_doc.get("outstanding_amount", 0))

        if total == 0:
            return "Initiated"  # fallback if somehow total is 0

        if outstanding == 0:
            return "Paid"
        elif outstanding < total:
            return "Partially Paid"
        else:
            return "Initiated"

    except Exception as e:
        frappe.log_error(f"get_outstanding_status error: {str(e)}", "Payment Request Sync Error")
        return "Initiated"

@frappe.whitelist()
def update_all_linked_payment_requests(doc, method=None):
    """
    On submission of a Payment Entry, update statuses of all linked Payment Requests.
    """
    try:
        # Ensure references is the child table field
        references = doc.get("references", [])
        if not references or not isinstance(references, list):
            frappe.log_error(f"Invalid references in {doc.doctype} {doc.name}: {references}", "Payment Request Sync Error")
            return

        for ref in references:
            # Safely access fields
            reference_doctype = ref.get("reference_doctype")
            reference_name = ref.get("reference_name")
            allocated_amount = flt(ref.get("allocated_amount", 0))

            if reference_doctype and reference_name and allocated_amount > 0:
                try:
                    precision = cint(ref.precision("allocated_amount") or 2)
                except Exception:
                    precision = 2

                allocated = flt(allocated_amount, precision)

                if allocated > 0:
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


import frappe
from erpnext.accounts.doctype.payment_request.payment_request import update_payment_requests_as_per_pe_references as original_update

def custom_update_payment_requests(references, cancel=None):
    """
    Override ERPNext's update_payment_requests_as_per_pe_references to ensure correct handling of references.
    """
    try:
        # If references is a document, extract its references child table
        if isinstance(references, frappe.model.Document) and references.doctype == "Payment Entry":
            references = references.get("references", [])
            frappe.log_error(f"Extracted references from Payment Entry {references.name}: {references}", "Payment Request Sync Debug")

        if not references or not isinstance(references, list):
            frappe.log_error(f"Invalid references in custom_update_payment_requests: {references}", "Payment Request Sync Error")
            return

        # Call the original function with the corrected references
        return original_update(references, cancel)

    except Exception as e:
        frappe.log_error(f"custom_update_payment_requests error: {str(e)}", "Payment Request Sync Error")