import frappe
from frappe.utils import flt

@frappe.whitelist()  # ✅ Required for JS access
def update_status_db(docname):
    try:
        doc = frappe.get_doc("Payment Request", docname)

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

        if doc.custom_status != new_status:
            frappe.db.set_value("Payment Request", docname, "custom_status", new_status)
            frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"update_status_db error for {docname}: {str(e)}")

@frappe.whitelist()
def get_outstanding_status(reference_doctype, reference_name):
    try:
        ref_doc = frappe.get_doc(reference_doctype, reference_name)

        if ref_doc.docstatus == 2:
            return "Cancelled"

        total = flt(ref_doc.get("total", 0)) or flt(ref_doc.get("base_grand_total", 0))
        outstanding = flt(ref_doc.get("outstanding_amount", 0))

        if outstanding == 0:
            return "Paid"
        elif outstanding < total:
            return "Partially Paid"
        else:
            return "Initiated"
    except Exception as e:
        frappe.log_error(f"get_outstanding_status error: {str(e)}")
        return "Initiated"
import frappe

@frappe.whitelist()
def update_all_linked_payment_requests(doc, method=None):
    try:
        refs = frappe.db.get_all(
            "Payment Request",
            filters={
                "reference_name": doc.name,
                "reference_doctype": doc.doctype,
                "docstatus": 1
            },
            pluck="name"
        )

        for pr in refs:
            update_status_db(pr)

    except Exception as e:
        frappe.log_error(f"update_all_linked_payment_requests error: {str(e)}")
