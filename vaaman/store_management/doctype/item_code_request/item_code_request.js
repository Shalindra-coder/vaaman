// Copyright (c) 2024, Pratul Tiwari and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item Code Request', {
	refresh: function(frm) {
		// Show a custom button to check if Item exists
		if (frm.doc.generated_code && frm.doc.workflow_state === 'Approved') {
			frm.add_custom_button(__('View Item'), function() {
				frappe.set_route('Form', 'Item', frm.doc.generated_code);
			});
		}
		
		// Make Generated Code editable only for Codification User
		if (frappe.user.has_role('Codification User') && 
			frm.doc.workflow_state === 'Pending Codification') {
			frm.set_df_property('generated_code', 'read_only', 0);
		} else {
			frm.set_df_property('generated_code', 'read_only', 1);
		}
	},
	
	is_asset_item: function(frm) {
		// Make asset_category mandatory if is_asset_item is checked
		if (frm.doc.is_asset_item) {
			frm.set_df_property('asset_category', 'reqd', 1);
		} else {
			frm.set_df_property('asset_category', 'reqd', 0);
			frm.set_value('asset_category', '');
		}
	}
});

