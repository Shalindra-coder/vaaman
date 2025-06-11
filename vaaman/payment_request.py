import frappe
from frappe.utils import flt

@frappe.whitelist()
def get_outstanding_status(reference_doctype, reference_name):
    try:
        ref_doc = frappe.get_doc(reference_doctype, reference_name)

        # If reference is cancelled
        if ref_doc.docstatus == 2:
            return "Cancelled"

        if hasattr(ref_doc, "outstanding_amount"):
            ref_total = flt(ref_doc.get("total", 0)) or flt(ref_doc.get("base_grand_total", 0))
            if flt(ref_doc.outstanding_amount) == 0:
                return "Paid"
            elif flt(ref_doc.outstanding_amount) < ref_total:
                return "Partially Paid"

        return "Initiated"

    except Exception as e:
        frappe.log_error(f"Error in get_outstanding_status: {str(e)}")
        return "Initiated"

@frappe.whitelist()
def update_status_db(docname):
    try:
        doc = frappe.get_doc("Payment Request", docname)

        if doc.docstatus == 2:
            new_status = "Cancelled"
        elif not doc.custom_custom_status or doc.workflow_state == "Draft":
            new_status = "Draft"
        elif doc.workflow_state == "Approval Pending By Management":
            new_status = "Ready to Pay"
        elif doc.docstatus == 1 and doc.reference_doctype and doc.reference_name:
            new_status = get_outstanding_status(doc.reference_doctype, doc.reference_name)
        else:
            new_status = "Initiated"

        if doc.custom_custom_status != new_status:
            # This will update status and set modified_by to current user
            frappe.db.set_value("Payment Request", docname, "custom_custom_status", new_status)

    except Exception as e:
        frappe.log_error(f"Failed to update custom status for Payment Request {docname}: {str(e)}")


def update_all_linked_payment_requests(doc, method=None):
    # Try to find Payment Requests linked to this Payment Entry
    refs = frappe.db.get_all("Payment Request", filters={
        "reference_name": doc.reference_name,
        "reference_doctype": doc.reference_doctype,
        "docstatus": 1
    }, pluck="name")

    for pr in refs:
        update_status_db(pr)
