import frappe
from frappe.utils import flt
@frappe.whitelist(allow_guest=True)
def update_payment_request_status(reference_doctype, reference_name):
    # Get all Payment Requests linked to this invoice
    payment_requests = frappe.get_all("Payment Request", filters={
        "reference_doctype": reference_doctype,
        "reference_name": reference_name,
        "docstatus": 1
    })

    for pr in payment_requests:
        doc = frappe.get_doc("Payment Request", pr.name)
        ref_doc = frappe.get_doc(reference_doctype, reference_name)

        if ref_doc.docstatus == 2:
            doc.custom_custom_status = "Cancelled"
        elif hasattr(ref_doc, "outstanding_amount"):
            if flt(ref_doc.outstanding_amount) == 0:
                doc.custom_custom_status = "Paid"
            elif flt(ref_doc.outstanding_amount) < flt(ref_doc.total or 0):
                doc.custom_custom_status = "Partially Paid"
            else:
                doc.custom_custom_status = "Initiated"

        doc.save(ignore_permissions=True)
