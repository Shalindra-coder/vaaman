frappe.ui.form.on("Payment Request", {
	party_type(frm) {
		vaaman_clear_payment_request_bank_fields(frm);
		vaaman_fetch_payment_request_bank_account(frm);
	},

	party(frm) {
		vaaman_clear_payment_request_bank_fields(frm);
		vaaman_fetch_payment_request_bank_account(frm);
	},

	custom_is_cash_vendor(frm) {
		if (frm.doc.custom_is_cash_vendor) {
			vaaman_clear_payment_request_bank_fields(frm);
		} else {
			vaaman_fetch_payment_request_bank_account(frm);
		}
	},
});

function vaaman_clear_payment_request_bank_fields(frm) {
	["bank_account", "bank", "bank_account_no", "branch_code", "iban", "account"].forEach((field) => {
		frm.set_value(field, "");
	});
}

function vaaman_fetch_payment_request_bank_account(frm) {
	if (!frm.doc.party_type || !frm.doc.party) {
		return;
	}

	if (frm.doc.custom_is_cash_vendor) {
		return;
	}

	const snapshot = `${frm.doc.party_type}::${frm.doc.party}`;
	frm._vaaman_pr_bank_fetch_token = (frm._vaaman_pr_bank_fetch_token || 0) + 1;
	const token = frm._vaaman_pr_bank_fetch_token;

	frappe.call({
		method: "erpnext.accounts.party.get_party_bank_account",
		args: {
			party_type: frm.doc.party_type,
			party: frm.doc.party,
		},
		callback(r) {
			if (token !== frm._vaaman_pr_bank_fetch_token) {
				return;
			}
			if (snapshot !== `${frm.doc.party_type}::${frm.doc.party}`) {
				return;
			}

			frm.set_value("bank_account", r.message || "");
		},
	});
}
