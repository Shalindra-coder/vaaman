frappe.listview_settings["Payment Request"] = {
	onload: function (listview) {
		$(document).on("click", ".text-muted.btn.btn-default.icon-btn", function (e) {
			listview.refresh();
		});
		const allowed_roles = [
			"HO Accounts User Payment",
			"HO Accounts User Sales",
			"HO Accounts User Purchase",
		];

		const user_roles = frappe.user_roles || [];

		const has_permission = allowed_roles.some((role) => user_roles.includes(role));

		if (!has_permission) {
			return; // Don't show the button
		}

		listview.page.add_inner_button(__("Make Draft Payment Entry"), function () {
			const selected_docs = listview.get_checked_items();

			if (!selected_docs.length) {
				frappe.msgprint(__("Please select at least one Payment Request"));
				return;
			}

			frappe.call({
				method: "vaaman.api.bulk_make_draft_payment_entries",
				args: {
					payment_requests: selected_docs.map((row) => row.name),
				},
				callback: function (r) {
					if (r.message) {
						let msg = "";
						if (r.message.success && r.message.success.length) {
							msg += "<b>Created Draft Payment Entries:</b><br>";
							r.message.success.forEach((pe) => {
								msg += `<a href="/app/payment-entry/${pe}" target="_blank">${pe}</a><br>`;
							});
						}
						if (r.message.failed && r.message.failed.length) {
							msg += "<br><b>Failed:</b><br>";
							r.message.failed.forEach((f) => {
								msg += `${f.name}: ${f.error}<br>`;
							});
						}
						frappe.msgprint(msg);
					}
				},
			});
		});
	},
	refresh: function (listview) {
		let selected_docs = listview.get_checked_items();
		selected_docs.forEach((doc) => {
			frappe.call({
				method: "vaaman.payment_request.update_status_db",
				args: {
					docname: doc.name,
				},
				callback: function (r) {
					if (r.exc) {
						frappe.msgprint({
							title: __("Error"),
							message: __("Failed to update status: {0}", [r.exc]),
							indicator: "red",
						});
						console.error("update_custom_status error:", r.exc);
						return;
					}
				},
			});
		});
	},
};
