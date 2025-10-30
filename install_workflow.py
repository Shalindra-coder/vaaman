#!/usr/bin/env python3
"""
Install Item Code Request Workflow and Roles
Run this from bench console:
bench --site vidhi console
>>> exec(open('/Users/pratul/frappe-bench/apps/vaaman/install_workflow.py').read())
"""

import frappe
import json

def create_roles():
	"""Create required roles"""
	print("\n" + "="*60)
	print("Creating Roles...")
	print("="*60)
	
	roles = [
		{"role_name": "Store User", "desk_access": 1},
		{"role_name": "Codification User", "desk_access": 1},
		{"role_name": "Item Manager", "desk_access": 1}
	]
	
	for role_data in roles:
		if not frappe.db.exists("Role", role_data["role_name"]):
			try:
				role = frappe.get_doc({
					"doctype": "Role",
					**role_data
				})
				role.insert(ignore_permissions=True)
				print(f"✓ Created role: {role_data['role_name']}")
			except Exception as e:
				print(f"✗ Error creating role {role_data['role_name']}: {str(e)}")
		else:
			print(f"✓ Role already exists: {role_data['role_name']}")
	
	frappe.db.commit()

def create_workflow_actions():
	"""Create workflow actions"""
	print("\n" + "="*60)
	print("Creating Workflow Actions...")
	print("="*60)
	
	actions = ["Submit", "Add Code", "Approve", "Reject"]
	
	for action_name in actions:
		if not frappe.db.exists("Workflow Action Master", action_name):
			try:
				action = frappe.get_doc({
					"doctype": "Workflow Action Master",
					"workflow_action_name": action_name
				})
				action.insert(ignore_permissions=True)
				print(f"✓ Created workflow action: {action_name}")
			except Exception as e:
				print(f"✗ Error creating workflow action {action_name}: {str(e)}")
		else:
			print(f"✓ Workflow action already exists: {action_name}")
	
	frappe.db.commit()

def create_workflow_states():
	"""Create workflow states"""
	print("\n" + "="*60)
	print("Creating Workflow States...")
	print("="*60)
	
	states = [
		{"workflow_state_name": "Draft", "style": "Info", "icon": "edit"},
		{"workflow_state_name": "Pending Codification", "style": "Warning", "icon": "pending-actions"},
		{"workflow_state_name": "Pending Approval", "style": "Primary", "icon": "assignment"},
		{"workflow_state_name": "Approved", "style": "Success", "icon": "check-circle"},
		{"workflow_state_name": "Rejected", "style": "Danger", "icon": "cancel"}
	]
	
	for state_data in states:
		if not frappe.db.exists("Workflow State", state_data["workflow_state_name"]):
			try:
				state = frappe.get_doc({
					"doctype": "Workflow State",
					**state_data
				})
				state.insert(ignore_permissions=True)
				print(f"✓ Created workflow state: {state_data['workflow_state_name']}")
			except Exception as e:
				print(f"✗ Error creating workflow state {state_data['workflow_state_name']}: {str(e)}")
		else:
			print(f"✓ Workflow state already exists: {state_data['workflow_state_name']}")
	
	frappe.db.commit()

def create_workflow():
	"""Create the Item Code Request Workflow"""
	print("\n" + "="*60)
	print("Creating Workflow...")
	print("="*60)
	
	workflow_name = "Item Code Request Workflow"
	
	# Delete existing workflow if any
	if frappe.db.exists("Workflow", workflow_name):
		print(f"! Workflow already exists. Deleting old workflow...")
		frappe.delete_doc("Workflow", workflow_name, ignore_permissions=True, force=True)
		frappe.db.commit()
	
	try:
		workflow = frappe.get_doc({
			"doctype": "Workflow",
			"workflow_name": workflow_name,
			"document_type": "Item Code Request",
			"is_active": 1,
			"send_email_alert": 0,
			"workflow_state_field": "workflow_state",
			"states": [
				{
					"doctype": "Workflow Document State",
					"state": "Draft",
					"doc_status": "0",
					"allow_edit": "Store User",
					"update_field": "workflow_state",
					"update_value": "Draft"
				},
				{
					"doctype": "Workflow Document State",
					"state": "Pending Codification",
					"doc_status": "1",
					"allow_edit": "Codification User",
					"update_field": "workflow_state",
					"update_value": "Pending Codification"
				},
				{
					"doctype": "Workflow Document State",
					"state": "Pending Approval",
					"doc_status": "1",
					"allow_edit": "Item Manager",
					"update_field": "workflow_state",
					"update_value": "Pending Approval"
				},
				{
					"doctype": "Workflow Document State",
					"state": "Approved",
					"doc_status": "1",
					"allow_edit": "Item Manager",
					"is_optional_state": 0,
					"update_field": "workflow_state",
					"update_value": "Approved"
				},
				{
					"doctype": "Workflow Document State",
					"state": "Rejected",
					"doc_status": "2",
					"allow_edit": "Item Manager",
					"is_optional_state": 0,
					"update_field": "workflow_state",
					"update_value": "Rejected"
				}
			],
			"transitions": [
				{
					"doctype": "Workflow Transition",
					"state": "Draft",
					"action": "Submit",
					"next_state": "Pending Codification",
					"allowed": "Store User",
					"allow_self_approval": 0
				},
				{
					"doctype": "Workflow Transition",
					"state": "Pending Codification",
					"action": "Add Code",
					"next_state": "Pending Approval",
					"allowed": "Codification User",
					"allow_self_approval": 0,
					"condition": "doc.generated_code"
				},
				{
					"doctype": "Workflow Transition",
					"state": "Pending Approval",
					"action": "Approve",
					"next_state": "Approved",
					"allowed": "Item Manager",
					"allow_self_approval": 0
				},
				{
					"doctype": "Workflow Transition",
					"state": "Pending Approval",
					"action": "Reject",
					"next_state": "Rejected",
					"allowed": "Item Manager",
					"allow_self_approval": 0
				}
			]
		})
		
		workflow.insert(ignore_permissions=True)
		frappe.db.commit()
		print(f"✓ Created workflow: {workflow_name}")
	except Exception as e:
		print(f"✗ Error creating workflow: {str(e)}")
		import traceback
		traceback.print_exc()

def main():
	"""Main installation function"""
	print("\n" + "#"*60)
	print("# Item Code Request System - Workflow Installation")
	print("#"*60)
	
	# Step 1: Create roles
	create_roles()
	
	# Step 2: Create workflow actions
	create_workflow_actions()
	
	# Step 3: Create workflow states
	create_workflow_states()
	
	# Step 4: Create workflow
	create_workflow()
	
	# Final message
	print("\n" + "="*60)
	print("INSTALLATION COMPLETE!")
	print("="*60)
	print("\nNext Steps:")
	print("1. Assign roles to users:")
	print("   - Go to User List → Select User → Add Role")
	print("   - Assign 'Store User', 'Codification User', or 'Item Manager'")
	print("\n2. Test the system:")
	print("   - Visit: /item-code-request")
	print("   - Create a test request")
	print("\n3. Clear cache:")
	print("   Run: bench --site vidhi clear-cache")
	print("="*60 + "\n")

if __name__ == "__main__":
	main()

