frappe.listview_settings['Payment Request'] = {
    onload: function(listview) {
        listview.page.add_inner_button(__('Make Draft Payment Entry'), function() {
            const selected_docs = listview.get_checked_items();

            if (!selected_docs.length) {
                frappe.msgprint(__('Please select at least one Payment Request'));
                return;
            }

            frappe.call({
                method: "vaaman.api.bulk_make_draft_payment_entries",
                args: {
                    payment_requests: selected_docs.map(row => row.name)
                },
                callback: function(r) {
                    if (r.message) {
                        let msg = '';
                        if (r.message.success && r.message.success.length) {
                            msg += "<b>Created Draft Payment Entries:</b><br>";
                            r.message.success.forEach(pe => {
                                msg += `<a href="/app/payment-entry/${pe}" target="_blank">${pe}</a><br>`;
                            });
                        }
                        if (r.message.failed && r.message.failed.length) {
                            msg += "<br><b>Failed:</b><br>";
                            r.message.failed.forEach(f => {
                                msg += `${f.name}: ${f.error}<br>`;
                            });
                        }
                        frappe.msgprint(msg);
                    }
                }
            });
        });
    }
};
