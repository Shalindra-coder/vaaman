frappe.listview_settings['Payment Entry'] = {
    onload(listview) {
        listview.page.add_action_item('Unreconcile Selected', async () => {
            const selected = listview.get_checked_items();

            if (!selected.length) {
                frappe.msgprint("Please select at least one Payment Entry.");
                return;
            }

            await frappe.call({
                method: "your_app_path.payment_entry_tools.bulk_unreconcile",
                args: {
                    payment_entry_names: selected.map(row => row.name)
                },
                callback: function(r) {
                    frappe.msgprint(r.message);
                    listview.refresh();
                }
            });
        });
    }
};
