import frappe

@frappe.whitelist()
def bulk_unreconcile(payment_entry_names):
    if isinstance(payment_entry_names, str):
        payment_entry_names = frappe.parse_json(payment_entry_names)

    for pe in payment_entry_names:
        # Find all GL Entries linked to this Payment Entry
        gl_entries = frappe.get_all("GL Entry", filters={
            "voucher_type": "Payment Entry",
            "voucher_no": pe
        }, fields=["name"])

        for gl in gl_entries:
            frappe.db.set_value("GL Entry", gl.name, "against_voucher_type", None)
            frappe.db.set_value("GL Entry", gl.name, "against_voucher", None)

    frappe.db.commit()

    return f"Unreconciled {len(payment_entry_names)} Payment Entries."
