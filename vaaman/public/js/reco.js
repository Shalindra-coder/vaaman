frappe.listview_settings['Payment Entry'] = {
    onload(listview) {
        listview.page.add_action_item('Unreconcile Selected', async () => {
            const selected = listview.get_checked_items();

            if (!selected.length) {
                frappe.msgprint("Please select at least one Payment Entry.");
                return;
            }

            frappe.call({
                method: "vaaman.reco.bulk_unreconcile_payment_entries",
                args: {
                    payment_entry_names: selected.map(row => row.name)
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.msgprint(`Unreconciled ${r.message.unreconciled} Payment Entries.<br>Errors: ${r.message.failed.join(", ")}`);
                    }
                    listview.refresh();
                }
            });
        });
    }
};
