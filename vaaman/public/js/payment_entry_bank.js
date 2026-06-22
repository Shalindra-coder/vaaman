frappe.ui.form.on("Payment Entry", {
	party_type(frm) {
		vaaman_clear_payment_entry_bank_fields(frm);
		vaaman_fetch_payment_entry_party_bank_account(frm);
	},

	party(frm) {
		vaaman_clear_payment_entry_bank_fields(frm);
		vaaman_fetch_payment_entry_party_bank_account(frm);
	},
});

function vaaman_clear_payment_entry_bank_fields(frm) {
	frm.set_value("party_bank_account", "");
	frm.set_value("bank_account", "");
}

function vaaman_fetch_payment_entry_party_bank_account(frm) {
	if (!frm.doc.party_type || !frm.doc.party) {
		return;
	}

	const snapshot = `${frm.doc.party_type}::${frm.doc.party}`;
	frm._vaaman_pe_bank_fetch_token = (frm._vaaman_pe_bank_fetch_token || 0) + 1;
	const token = frm._vaaman_pe_bank_fetch_token;

	frappe.call({
		method: "erpnext.accounts.party.get_party_bank_account",
		args: {
			party_type: frm.doc.party_type,
			party: frm.doc.party,
		},
		callback(r) {
			if (token !== frm._vaaman_pe_bank_fetch_token) {
				return;
			}
			if (snapshot !== `${frm.doc.party_type}::${frm.doc.party}`) {
				return;
			}

			frm.set_value("party_bank_account", r.message || "");
		},
	});
}
