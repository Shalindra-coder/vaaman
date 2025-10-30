# Item Code Request System

## Overview

This is a complete Item Code Request management system built for ERPNext in the Vaaman custom app. It allows Store Users to request new item codes via a web form, Codification Personnel to assign item codes, and Item Managers to approve requests. Once approved, items are automatically created in ERPNext.

## Components Created

### 1. Module: Store Management
- Added to `modules.txt`
- Contains all Item Code Request related doctypes, web forms, and workflows

### 2. Doctype: Item Code Request
**Location:** `vaaman/store_management/doctype/item_code_request/`

**Auto-naming:** ITMREQ-.#####

**Fields:**
- Item Name (Data, Required)
- HSN Code (Data, Required)
- Description (Small Text)
- Item Group (Link → Item Group, Required)
- Is Stock Item (Check, Default=1)
- Is Asset Item (Check, Default=0)
- Asset Category (Link → Asset Category, shown only when Is Asset Item is checked)
- Generated Code (Data, Read Only - editable by Codification User in specific workflow state)
- Workflow State (Link, Read Only)

**Permissions:**
- **Store User:** Create, Read, Write (own documents), Delete
- **Codification User:** Read, Write
- **Item Manager:** Read, Write, Submit, Cancel, Amend

**Validation:**
- Asset Category is required when Is Asset Item is checked

**Automatic Item Creation:**
- When workflow state is "Approved", a new Item is automatically created in ERPNext
- Item creation happens in `on_update_after_submit()` method
- Prevents duplicate items from being created

### 3. Web Form: Item Code Request Form
**Location:** `vaaman/store_management/web_form/item_code_request_form/`

**URL:** `/item-code-request`

**Features:**
- Public access (login required)
- Store users can submit requests
- Shows user's own requests in list view
- Fields visible to users:
  - Item Name
  - HSN Code
  - Description
  - Item Group
  - Is Stock Item
  - Is Asset Item
  - Asset Category (conditional)

**Hidden from web form users:**
- Generated Code (filled by Codification User)
- Workflow State (managed by workflow)

### 4. Workflow: Item Code Request Workflow
**Location:** `vaaman/fixtures/workflow.json` and `vaaman/fixtures/workflow_state.json`

**States:**

1. **Draft** (doc_status: 0)
   - Created by Store User
   - Allows: Store User to edit

2. **Pending Codification** (doc_status: 1)
   - After Store User submits
   - Allows: Codification User to edit and add Generated Code

3. **Pending Approval** (doc_status: 1)
   - After Codification User adds code
   - Allows: Item Manager to approve or reject

4. **Approved** (doc_status: 1)
   - Final approval state
   - Triggers automatic Item creation

5. **Rejected** (doc_status: 2)
   - Request rejected by Item Manager

**Transitions:**

1. Draft → Pending Codification
   - Action: "Submit"
   - Allowed: Store User

2. Pending Codification → Pending Approval
   - Action: "Add Code"
   - Allowed: Codification User
   - Condition: Generated Code must be filled

3. Pending Approval → Approved
   - Action: "Approve"
   - Allowed: Item Manager
   - Triggers: Automatic Item creation

4. Pending Approval → Rejected
   - Action: "Reject"
   - Allowed: Item Manager

### 5. Automatic Item Creation
**Location:** Implemented in `item_code_request.py`

**Trigger:** When workflow state changes to "Approved"

**Item Mapping:**
- Item Code = Generated Code
- Item Name = Item Name
- Item Group = Item Group
- Description = Description
- GST HSN Code = HSN Code
- Is Stock Item = Is Stock Item
- Is Fixed Asset = Is Asset Item
- Asset Category = Asset Category (if Is Asset Item is checked)
- Disabled = 0 (enabled by default)

**Safety Features:**
- Checks if item already exists before creation
- Uses `ignore_permissions=True` to ensure creation even if user lacks direct Item creation permissions
- Logs errors if creation fails
- Adds a comment to the Item Code Request document tracking the item creation

## Installation & Setup

### 1. Install/Update the Vaaman App

```bash
cd /Users/pratul/frappe-bench
bench --site [your-site] migrate
```

This will:
- Create the Item Code Request doctype
- Install the workflow and workflow states
- Set up the web form

### 2. Create Required Roles

Make sure these roles exist in your ERPNext instance:

```bash
bench --site [your-site] console
```

Then run:

```python
import frappe

roles = ["Store User", "Codification User", "Item Manager"]
for role in roles:
    if not frappe.db.exists("Role", role):
        doc = frappe.get_doc({
            "doctype": "Role",
            "role_name": role
        })
        doc.insert()
        frappe.db.commit()
```

### 3. Assign Roles to Users

Go to User list and assign appropriate roles:
- **Store Users** → "Store User" role
- **Codification Personnel** → "Codification User" role
- **Item Managers** → "Item Manager" role

### 4. Verify Web Form

Visit: `http://[your-site]/item-code-request`

You should see the Item Code Request form.

### 5. Verify Workflow

1. Go to: Doctype List → Item Code Request
2. Create a new document
3. You should see workflow actions based on your role

## Usage Workflow

### For Store Users:

1. **Access the Web Form:**
   - Navigate to `/item-code-request`
   - Or create a new Item Code Request from the Doctype list

2. **Fill in the Form:**
   - Item Name: Enter the name of the item
   - HSN Code: Enter the GST HSN code
   - Description: Provide details about the item
   - Item Group: Select appropriate item group
   - Is Stock Item: Check if this is a stock item
   - Is Asset Item: Check if this is an asset
   - Asset Category: Select if it's an asset (required when Is Asset Item is checked)

3. **Submit:**
   - Click "Submit Request"
   - The request moves to "Pending Codification" state
   - Store User receives confirmation

### For Codification Users:

1. **View Pending Requests:**
   - Go to Item Code Request list
   - Filter by Workflow State = "Pending Codification"

2. **Add Generated Code:**
   - Open the document
   - Fill in the "Generated Code" field with the assigned item code
   - Click "Add Code" workflow action
   - Request moves to "Pending Approval" state

### For Item Managers:

1. **View Pending Approvals:**
   - Go to Item Code Request list
   - Filter by Workflow State = "Pending Approval"

2. **Review and Approve:**
   - Open the document
   - Review all details
   - Click "Approve" workflow action
   - Item is automatically created in ERPNext
   - Success message appears

3. **Or Reject:**
   - Click "Reject" workflow action if needed
   - Request moves to "Rejected" state

## Customization Options

### 1. Modify Fields
Edit the doctype JSON file:
```
vaaman/store_management/doctype/item_code_request/item_code_request.json
```

### 2. Change Workflow States/Transitions
Edit the workflow fixture:
```
vaaman/fixtures/workflow.json
```

After making changes, run:
```bash
bench --site [your-site] migrate
```

### 3. Customize Item Creation Logic
Edit the `create_item()` method in:
```
vaaman/store_management/doctype/item_code_request/item_code_request.py
```

### 4. Add Email Notifications
Update `hooks.py` to enable email notifications:
```python
# In the workflow fixture, set:
"send_email_alert": 1
```

Then create email templates for each workflow transition.

### 5. Add Custom Validations
Add validation logic in the `validate()` method of `ItemCodeRequest` class.

## Testing

Run unit tests:
```bash
cd /Users/pratul/frappe-bench
bench --site [your-site] run-tests --app vaaman --doctype "Item Code Request"
```

## File Structure

```
apps/vaaman/
├── vaaman/
│   ├── modules.txt                          # Added "Store Management"
│   ├── hooks.py                             # Added fixtures and doc_events
│   ├── fixtures/
│   │   ├── workflow.json                    # Workflow definition
│   │   └── workflow_state.json              # Workflow states
│   └── store_management/
│       ├── __init__.py
│       ├── doctype/
│       │   ├── __init__.py
│       │   └── item_code_request/
│       │       ├── __init__.py
│       │       ├── item_code_request.json   # Doctype definition
│       │       ├── item_code_request.py     # Controller with business logic
│       │       ├── item_code_request.js     # Client-side script
│       │       └── test_item_code_request.py # Unit tests
│       └── web_form/
│           ├── __init__.py
│           └── item_code_request_form/
│               ├── __init__.py
│               └── item_code_request_form.json # Web form definition
└── ITEM_CODE_REQUEST_README.md             # This file
```

## Troubleshooting

### Issue: Web form not showing
**Solution:** 
```bash
bench --site [your-site] migrate
bench clear-cache
bench restart
```

### Issue: Workflow not working
**Solution:**
1. Check if roles are assigned correctly
2. Verify workflow is active in Workflow list
3. Check if document is in submittable state

### Issue: Item not created automatically
**Solution:**
1. Check error logs: `bench --site [your-site] logs`
2. Verify Generated Code field is filled
3. Check if item with same code already exists
4. Verify Item Manager has permissions to create Items

### Issue: "Generated Code" field not editable
**Solution:**
- Only Codification Users can edit this field
- Only editable in "Pending Codification" workflow state
- JavaScript controls this behavior in `item_code_request.js`

## Support & Contribution

For issues or enhancements:
1. Check ERPNext logs: `bench --site [your-site] logs`
2. Review the code in the files mentioned above
3. Modify as needed for your specific requirements

## License

MIT License - Same as the Vaaman app

## Author

Pratul Tiwari
Email: ptpratul2@gmail.com

