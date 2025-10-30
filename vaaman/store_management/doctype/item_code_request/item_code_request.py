# Copyright (c) 2024, Pratul Tiwari and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ItemCodeRequest(Document):
	def validate(self):
		"""Validate the document before saving"""
		# If is_asset_item is checked, asset_category should be required
		if self.is_asset_item and not self.asset_category:
			frappe.throw("Asset Category is required when Is Asset Item is checked")
	
	def on_submit(self):
		"""Handle document submission"""
		# Check if workflow state is Approved and create Item
		if self.workflow_state == "Approved":
			self.create_item()
	
	def on_update_after_submit(self):
		"""Handle updates after submission (for workflow transitions)"""
		# Create Item when workflow state changes to Approved
		if self.workflow_state == "Approved" and not self.has_linked_item():
			self.create_item()
	
	def create_item(self):
		"""Create a new Item in ERPNext"""
		if not self.generated_code:
			frappe.throw("Generated Code is required to create an Item")
		
		# Check if item already exists
		if frappe.db.exists("Item", self.generated_code):
			frappe.msgprint(f"Item {self.generated_code} already exists in ERPNext.")
			return
		
		try:
			item = frappe.get_doc({
				"doctype": "Item",
				"item_code": self.generated_code,
				"item_name": self.item_name,
				"item_group": self.item_group,
				"description": self.description,
				"gst_hsn_code": self.hsn_code,
				"is_stock_item": self.is_stock_item,
				"is_fixed_asset": self.is_asset_item,
				"asset_category": self.asset_category if self.is_asset_item else None,
				"disabled": 0
			})
			item.insert(ignore_permissions=True)
			frappe.msgprint(f"Item {self.generated_code} created successfully in ERPNext.")
			
			# Add a comment to track the creation
			self.add_comment(
				"Info",
				f"Item {self.generated_code} was created in ERPNext"
			)
			
		except Exception as e:
			frappe.log_error(f"Error creating Item from Item Code Request {self.name}: {str(e)}")
			frappe.throw(f"Failed to create Item: {str(e)}")
	
	def has_linked_item(self):
		"""Check if an Item already exists with the generated code"""
		if self.generated_code:
			return frappe.db.exists("Item", self.generated_code)
		return False


# Hook functions for doc_events
def on_submit_hook(doc, method):
	"""Hook function called on submit"""
	doc.on_submit()


def on_update_after_submit_hook(doc, method):
	"""Hook function called on update after submit"""
	doc.on_update_after_submit()

