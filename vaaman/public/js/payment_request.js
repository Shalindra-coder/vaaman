frappe.ui.form.on('Payment Request', {
    onload(frm) {
        // Only update status — avoid reload to prevent infinite loop
        update_custom_status(frm);
    },
});

function update_custom_status(frm, save_if_changed = false) {
    if (!frm.doc.name) return;

    frappe.call({
        method: "vaaman.payment_request.update_status_db",
        args: {
            docname: frm.doc.name
        },
        callback: function(r) {
            if (!r.exc && save_if_changed) {
                frm.save(); // only save if needed
            }
        }
    });
}
