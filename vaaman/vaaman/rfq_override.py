import importlib
import frappe

from erpnext.buying.doctype.request_for_quotation.request_for_quotation import RequestforQuotation

RFQ_MODULE = "erpnext.buying.doctype.request_for_quotation.request_for_quotation"


class CustomRFQ(RequestforQuotation):
    def update_supplier_contact(self, rfq_supplier, link):

        update_password_link, contact = "", ""

        if frappe.db.exists("User", rfq_supplier.email_id):
            user = frappe.get_doc("User", rfq_supplier.email_id)

            # reset password link for existing user
            user.reset_password()
            update_password_link = frappe.utils.get_url(
                f"/update-password?key={user.reset_password_key}"
            )
        else:
            user, update_password_link = self.create_user(rfq_supplier, link)

        contact = self.link_supplier_contact(rfq_supplier, user)

        return update_password_link, contact
    
    
def patch_rfq():
    module = importlib.import_module(RFQ_MODULE)
    module.RequestforQuotation = CustomRFQ    