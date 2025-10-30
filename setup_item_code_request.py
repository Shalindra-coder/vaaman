#!/usr/bin/env python3
"""
Setup script for Item Code Request System
Run this after installing the vaaman app to ensure all roles and configurations are set up
"""

import frappe


def setup_roles():
	"""Create required roles if they don't exist"""
	print("Setting up roles...")
	roles = ["Store User", "Codification User", "Item Manager"]
	
	for role in roles:
		if not frappe.db.exists("Role", role):
			try:
				doc = frappe.get_doc({
					"doctype": "Role",
					"role_name": role,
					"desk_access": 1
				})
				doc.insert(ignore_permissions=True)
				print(f"✓ Created role: {role}")
			except Exception as e:
				print(f"✗ Error creating role {role}: {str(e)}")
		else:
			print(f"✓ Role already exists: {role}")
	
	frappe.db.commit()


def verify_doctype():
	"""Verify that Item Code Request doctype exists"""
	print("\nVerifying doctype...")
	if frappe.db.exists("DocType", "Item Code Request"):
		print("✓ Item Code Request doctype exists")
		return True
	else:
		print("✗ Item Code Request doctype not found. Please run 'bench migrate' first.")
		return False


def verify_workflow():
	"""Verify that the workflow exists"""
	print("\nVerifying workflow...")
	if frappe.db.exists("Workflow", "Item Code Request Workflow"):
		print("✓ Item Code Request Workflow exists")
		
		# Check if workflow is active
		workflow = frappe.get_doc("Workflow", "Item Code Request Workflow")
		if workflow.is_active:
			print("✓ Workflow is active")
		else:
			print("! Workflow exists but is not active. Activating...")
			workflow.is_active = 1
			workflow.save(ignore_permissions=True)
			frappe.db.commit()
			print("✓ Workflow activated")
		return True
	else:
		print("✗ Workflow not found. Please run 'bench migrate' first.")
		return False


def verify_web_form():
	"""Verify that the web form exists"""
	print("\nVerifying web form...")
	if frappe.db.exists("Web Form", "Item Code Request Form"):
		print("✓ Item Code Request Form exists")
		
		# Check if web form is published
		web_form = frappe.get_doc("Web Form", "Item Code Request Form")
		if web_form.published:
			print("✓ Web form is published")
			print(f"  Access it at: /item-code-request")
		else:
			print("! Web form exists but is not published. Publishing...")
			web_form.published = 1
			web_form.save(ignore_permissions=True)
			frappe.db.commit()
			print("✓ Web form published")
		return True
	else:
		print("✗ Web form not found. Please run 'bench migrate' first.")
		return False


def create_sample_item_group():
	"""Create a sample item group for testing"""
	print("\nCreating sample item group...")
	if not frappe.db.exists("Item Group", "Sample Items"):
		try:
			doc = frappe.get_doc({
				"doctype": "Item Group",
				"item_group_name": "Sample Items",
				"parent_item_group": "All Item Groups",
				"is_group": 0
			})
			doc.insert(ignore_permissions=True)
			frappe.db.commit()
			print("✓ Created sample item group: Sample Items")
		except Exception as e:
			print(f"✗ Error creating sample item group: {str(e)}")
	else:
		print("✓ Sample item group already exists")


def print_next_steps():
	"""Print next steps for the user"""
	print("\n" + "="*60)
	print("SETUP COMPLETE!")
	print("="*60)
	print("\nNext Steps:")
	print("1. Assign roles to users:")
	print("   - Go to: User List → Select User → Add Role")
	print("   - Assign 'Store User' to store personnel")
	print("   - Assign 'Codification User' to codification team")
	print("   - Assign 'Item Manager' to managers")
	print("\n2. Access the web form:")
	print("   - URL: http://[your-site]/item-code-request")
	print("\n3. Test the workflow:")
	print("   - Create a request as Store User")
	print("   - Add code as Codification User")
	print("   - Approve as Item Manager")
	print("   - Verify item is created automatically")
	print("\n4. Read the documentation:")
	print("   - See ITEM_CODE_REQUEST_README.md for detailed instructions")
	print("="*60 + "\n")


def main():
	"""Main setup function"""
	print("\n" + "="*60)
	print("Item Code Request System Setup")
	print("="*60 + "\n")
	
	# Setup roles
	setup_roles()
	
	# Verify components
	doctype_ok = verify_doctype()
	workflow_ok = verify_workflow()
	web_form_ok = verify_web_form()
	
	# Create sample data
	if doctype_ok:
		create_sample_item_group()
	
	# Print next steps
	if doctype_ok and workflow_ok and web_form_ok:
		print_next_steps()
	else:
		print("\n" + "!"*60)
		print("SETUP INCOMPLETE!")
		print("!"*60)
		print("\nPlease run the following command first:")
		print("  bench --site [your-site] migrate")
		print("\nThen run this script again.")
		print("!"*60 + "\n")


if __name__ == "__main__":
	frappe.init(site="[your-site]")
	frappe.connect()
	main()
	frappe.destroy()

