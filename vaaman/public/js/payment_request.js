frappe.ui.form.on('Payment Request', {
    refresh(frm) {
        // Update custom_status on form refresh, but only if the document exists
        if (frm.doc.name && !frm.is_new()) {
            update_custom_status(frm);
        }
    },
    workflow_state(frm) {
        // Update custom_status when workflow_state changes
        if (frm.doc.name && !frm.is_new()) {
            update_custom_status(frm, true);
        }
    },
    docstatus(frm) {
        // Update custom_status when docstatus changes (e.g., submit or cancel)
        if (frm.doc.name && !frm.is_new()) {
            update_custom_status(frm, true);
        }
    },
    reference_doctype(frm) {
        // Update custom_status when reference_doctype changes
        if (frm.doc.name && !frm.is_new()) {
            update_custom_status(frm, true);
        }
    },
    reference_name(frm) {
        // Update custom_status when reference_name changes
        if (frm.doc.name && !frm.is_new()) {
            update_custom_status(frm, true);
        }
    }
});

function update_custom_status(frm, save_if_changed = false) {
    if (!frm.doc.name || frm.is_new()) return;

    frappe.call({
        method: "vaaman.payment_request.update_status_db",
        args: {
            docname: frm.doc.name
        },
        freeze: true, // Show a loading indicator
        freeze_message: __("Updating status..."),
        callback: function(r) {
            if (r.exc) {
                frappe.msgprint({
                    title: __("Error"),
                    message: __("Failed to update status: {0}", [r.exc]),
                    indicator: "red"
                });
                console.error("update_custom_status error:", r.exc);
                return;
            }

            // Reload the form to reflect changes only if custom_status changed
            if (save_if_changed && r.message && r.message !== frm.doc.custom_status) {
                frm.reload_doc();
            }
        },
        error: function(err) {
            frappe.msgprint({
                title: __("Error"),
                message: __("An unexpected error occurred while updating status."),
                indicator: "red"
            });
            console.error("update_custom_status error:", err);
        }
    });
}