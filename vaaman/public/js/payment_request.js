// ✅ Register realtime listener globally
frappe.realtime.on("payment_request_status_update", function (data) {
	if (cur_list && cur_list.doctype === "Payment Request") {
		// Refresh the list if it's open
		cur_list.refresh();
	}

	if (
		cur_frm &&
		cur_frm.doc &&
		cur_frm.doc.doctype === "Payment Request" &&
		cur_frm.doc.name === data.payment_request
	) {
		// Refresh the form if it's open for the same document
		cur_frm.reload_doc();
	}
});

// ✅ Form triggers
frappe.ui.form.on("Payment Request", {
	refresh(frm) {
		// Update custom_status on form refresh
		if (frm.doc.name && !frm.is_new()) {
			update_custom_status(frm);
		}
	},
	workflow_state(frm) {
		// Update when workflow_state changes
		if (frm.doc.name && !frm.is_new()) {
			update_custom_status(frm, true);
		}
	},
	docstatus(frm) {
		// Update when docstatus changes
		if (frm.doc.name && !frm.is_new()) {
			update_custom_status(frm, true);
		}
	},
	reference_doctype(frm) {
		// Update when reference_doctype changes
		if (frm.doc.name && !frm.is_new()) {
			update_custom_status(frm, true);
		}
	},
	reference_name(frm) {
		// Update when reference_name changes
		if (frm.doc.name && !frm.is_new()) {
			update_custom_status(frm, true);
		}
	},
});

// ✅ Helper function
function update_custom_status(frm, save_if_changed = false) {
	if (!frm.doc.name || frm.is_new()) return;

	const previous_status = frm.doc.custom_status;

	frappe.call({
		method: "vaaman.payment_request.update_status_db",
		args: {
			docname: frm.doc.name,
		},
		freeze: true,
		freeze_message: __("Updating status..."),

		callback: function (r) {
			if (r.message) {
				frm.set_value("custom_status", r.message);
				frm.refresh_field("custom_status");
			}

			if (r.exc) {
				frappe.msgprint({
					title: __("Error"),
					message: __("Failed to update status: {0}", [r.exc]),
					indicator: "red",
				});
				console.error("update_custom_status error:", r.exc);
				return;
			}

			// Reload the form only if the status changed
			if (save_if_changed && r.message && r.message !== previous_status) {
				frm.reload_doc();
			}
		},
		error: function (err) {
			frappe.msgprint({
				title: __("Error"),
				message: __("An unexpected error occurred while updating status."),
				indicator: "red",
			});
			console.error("update_custom_status error:", err);
		},
	});
}
