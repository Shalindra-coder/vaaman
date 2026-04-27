// ✅ Register realtime listener once
if (!window.__vaaman_pr_status_listener_registered) {
	window.__vaaman_pr_status_listener_registered = true;
	frappe.realtime.on("payment_request_status_update", function (data) {
		if (cur_list && cur_list.doctype === "Payment Request") {
			// Keep list live, but do not thrash refresh.
			clearTimeout(window.__vaaman_pr_list_refresh_timer);
			window.__vaaman_pr_list_refresh_timer = setTimeout(() => cur_list.refresh(), 400);
		}

		if (
			cur_frm &&
			cur_frm.doc &&
			cur_frm.doc.doctype === "Payment Request" &&
			cur_frm.doc.name === data.payment_request
		) {
			// Patch field value without reload_doc() to avoid refresh loops.
			if (data.new_status != null && data.new_status !== cur_frm.doc.custom_status) {
				cur_frm.set_value("custom_status", data.new_status);
				cur_frm.refresh_field("custom_status");
			}
		}
	});
}

// ✅ Form triggers
frappe.ui.form.on("Payment Request", {
	onload(frm) {
		// Sync once on open; refresh can fire many times (save/reload/realtime).
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
	if (frm.__vaaman_pr_status_inflight) return;

	frm.__vaaman_pr_status_inflight = true;
	const prev_custom_status = frm.doc.custom_status;

	frappe.call({
		method: "vaaman.payment_request.update_status_db",
		args: {
			docname: frm.doc.name,
		},
		always: function () {
			frm.__vaaman_pr_status_inflight = false;
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

			if (!r.message || r.message === prev_custom_status) {
				return;
			}

			// DB is already updated by server; do not save/reload here.
			frm.set_value("custom_status", r.message);
			frm.refresh_field("custom_status");
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
