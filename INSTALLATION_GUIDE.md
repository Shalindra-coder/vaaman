# Item Code Request System - Installation Guide

## Quick Installation Steps

### 1. Migrate the Database

This will install the Item Code Request doctype, workflow, and web form:

```bash
cd /Users/pratul/frappe-bench
bench --site [your-site-name] migrate
```

Replace `[your-site-name]` with your actual site name (e.g., `vidhi`).

### 2. Clear Cache and Restart

```bash
bench clear-cache
bench restart
```

### 3. Run Setup Script (Optional but Recommended)

The setup script will create required roles and verify the installation:

```bash
bench --site [your-site-name] console
```

Then in the console:

```python
exec(open('/Users/pratul/frappe-bench/apps/vaaman/setup_item_code_request.py').read())
```

Or manually:

```python
import frappe
frappe.init(site="[your-site-name]")
frappe.connect()

# Create roles
roles = ["Store User", "Codification User", "Item Manager"]
for role in roles:
    if not frappe.db.exists("Role", role):
        doc = frappe.get_doc({
            "doctype": "Role",
            "role_name": role,
            "desk_access": 1
        })
        doc.insert(ignore_permissions=True)
        print(f"Created role: {role}")

frappe.db.commit()
frappe.destroy()
```

### 4. Assign Roles to Users

1. Go to: **User List** (search "User" in awesome bar)
2. Select a user
3. Scroll to "Roles" section
4. Add appropriate roles:
   - **Store User** - For personnel who request items
   - **Codification User** - For personnel who assign item codes
   - **Item Manager** - For managers who approve requests

### 5. Verify Installation

#### Check Doctype:
```bash
bench --site [your-site-name] console
```
```python
import frappe
frappe.init(site="[your-site-name]")
frappe.connect()
print(frappe.db.exists("DocType", "Item Code Request"))
frappe.destroy()
```

Should return: `Item Code Request`

#### Check Workflow:
1. Go to: **Workflow List** (search "Workflow" in awesome bar)
2. Look for: **Item Code Request Workflow**
3. Ensure it's marked as **Active**

#### Check Web Form:
1. Go to: **Web Form List** (search "Web Form" in awesome bar)
2. Look for: **Item Code Request Form**
3. Ensure it's marked as **Published**
4. Or visit directly: `http://[your-site]/item-code-request`

### 6. Test the System

#### As Store User:
1. Visit: `http://[your-site]/item-code-request`
2. Fill in the form:
   - Item Name: Test Item 001
   - HSN Code: 1234
   - Description: This is a test item
   - Item Group: (select any)
   - Is Stock Item: ✓ (checked)
   - Is Asset Item: ☐ (unchecked)
3. Click **Submit Request**
4. You should see: "Request Submitted" message

#### As Codification User:
1. Go to: **Item Code Request** list
2. Open the request created above
3. Status should be: **Pending Codification**
4. Fill in **Generated Code**: TEST-ITEM-001
5. Click **Add Code** button
6. Status changes to: **Pending Approval**

#### As Item Manager:
1. Go to: **Item Code Request** list
2. Open the same request
3. Status should be: **Pending Approval**
4. Click **Approve** button
5. You should see: "Item TEST-ITEM-001 created successfully in ERPNext"
6. Status changes to: **Approved**

#### Verify Item Creation:
1. Go to: **Item** list (search "Item" in awesome bar)
2. Search for: **TEST-ITEM-001**
3. Open the item and verify:
   - Item Code: TEST-ITEM-001
   - Item Name: Test Item 001
   - HSN Code: 1234
   - Description: This is a test item
   - Is Stock Item: ✓

## Troubleshooting

### Error: "DocType Item Code Request not found"

**Solution:**
```bash
bench --site [your-site-name] migrate
bench clear-cache
bench restart
```

### Error: "Workflow not working"

**Solution:**
1. Check if workflow is active:
   - Go to Workflow List
   - Open "Item Code Request Workflow"
   - Ensure "Is Active" is checked
   - Save

2. Check role assignments:
   - Go to User List
   - Verify users have correct roles assigned

### Error: "Web form not accessible"

**Solution:**
1. Check if web form is published:
   - Go to Web Form List
   - Open "Item Code Request Form"
   - Ensure "Published" is checked
   - Save

2. Clear cache:
```bash
bench clear-cache
bench restart
```

### Error: "Permission denied"

**Solution:**
1. Verify role assignments for the user
2. Check permissions in the Item Code Request doctype:
   - Go to DocType List
   - Open "Item Code Request"
   - Scroll to "Permissions" section
   - Verify roles have appropriate permissions

### Error: "Item not created automatically"

**Solution:**
1. Check if Generated Code field is filled
2. Check if workflow state is "Approved"
3. Check error logs:
```bash
bench --site [your-site-name] logs
```

4. Check if item already exists:
   - Go to Item List
   - Search for the generated code

### Error: "Generated Code field is read-only"

**Expected Behavior:** 
- This field is read-only by default
- Only Codification Users can edit it
- Only editable when workflow state is "Pending Codification"
- This is controlled by JavaScript in the doctype

**Solution:** 
- Make sure you're logged in as a Codification User
- Make sure the document is in "Pending Codification" state

## Advanced Configuration

### Enable Email Notifications

1. Go to: **Workflow** List
2. Open: "Item Code Request Workflow"
3. Check: "Send Email Alert"
4. Save

Then create email templates for each transition:
- Go to: **Email Template** List
- Create templates for: Submit, Add Code, Approve, Reject

### Customize Fields

Edit the doctype:
```bash
bench --site [your-site-name] console
```
```python
import frappe
frappe.init(site="[your-site-name]")
frappe.connect()

doc = frappe.get_doc("DocType", "Item Code Request")
# Make changes to doc.fields
doc.save()
frappe.db.commit()
frappe.destroy()
```

Or use Desk:
1. Enable Developer Mode in site_config.json:
```bash
bench --site [your-site-name] set-config developer_mode 1
bench restart
```

2. Go to DocType List → Item Code Request → Edit

### Add Custom Scripts

Create a server script:
1. Go to: **Server Script** List
2. Create new script
3. Document Events → Item Code Request → Before Submit
4. Add your custom Python code

### Modify Workflow

1. Go to: **Workflow** List
2. Open: "Item Code Request Workflow"
3. Add/Modify states and transitions
4. Save

## Files Structure Reference

```
apps/vaaman/
├── vaaman/
│   ├── modules.txt                          # Contains "Store Management"
│   ├── hooks.py                             # Contains fixtures and doc_events
│   ├── fixtures/
│   │   ├── workflow.json                    # Workflow definition
│   │   └── workflow_state.json              # Workflow states
│   └── store_management/
│       ├── doctype/
│       │   └── item_code_request/
│       │       ├── item_code_request.json   # Doctype definition
│       │       ├── item_code_request.py     # Server-side logic
│       │       ├── item_code_request.js     # Client-side logic
│       │       └── test_item_code_request.py
│       └── web_form/
│           └── item_code_request_form/
│               └── item_code_request_form.json
├── ITEM_CODE_REQUEST_README.md              # Detailed documentation
├── INSTALLATION_GUIDE.md                    # This file
└── setup_item_code_request.py               # Setup script
```

## Need Help?

- Check logs: `bench --site [your-site-name] logs`
- Read documentation: `ITEM_CODE_REQUEST_README.md`
- Review code in files mentioned above

## Support

For issues or questions:
- Email: ptpratul2@gmail.com
- Check ERPNext Community: https://discuss.erpnext.com/

