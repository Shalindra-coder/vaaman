import frappe

def get_party_account_from_master(party_type, party, company):
    """
    Fallback method to get party account from Party Account table.
    """
    if not party_type or not party:
        frappe.throw("Missing party type or party")

    account = frappe.db.get_value(
        "Party Account",
        {
            "parenttype": party_type,
            "parent": party,
            "company": company
        },
        "account"
    )

    if not account:
        frappe.throw(f"No party account found for {party_type} '{party}' in company '{company}'")

    return account
