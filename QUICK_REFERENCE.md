# Item Code Request System - Quick Reference Card

## 🚀 Quick Start

```bash
# Install
cd /Users/pratul/frappe-bench
bench --site [your-site] migrate
bench clear-cache && bench restart

# Create Roles (via console)
bench --site [your-site] console
exec(open('/Users/pratul/frappe-bench/apps/vaaman/setup_item_code_request.py').read())
```

## 📋 Roles & Permissions

| Role | Permissions |
|------|------------|
| **Store User** | Create, Read, Write (own), Delete |
| **Codification User** | Read, Write, Edit Generated Code |
| **Item Manager** | Read, Write, Submit, Approve, Reject |

## 🔄 Workflow States

```
Draft → Pending Codification → Pending Approval → Approved
                                               └→ Rejected
```

| State | Who Can Act | Action Available |
|-------|-------------|------------------|
| Draft | Store User | Submit |
| Pending Codification | Codification User | Add Code |
| Pending Approval | Item Manager | Approve / Reject |
| Approved | System | Auto-create Item |
| Rejected | - | End state |

## 📝 Required Fields

### For Store User (Web Form)
- ✅ Item Name
- ✅ HSN Code
- ✅ Item Group
- ⭕ Description (optional)
- ☑️ Is Stock Item (default: yes)
- ☑️ Is Asset Item (default: no)
- ⭕ Asset Category (required if Is Asset Item)

### For Codification User
- ✅ Generated Code (must fill before Add Code action)

## 🌐 URLs & Access Points

| Resource | URL/Location |
|----------|-------------|
| Web Form | `http://[your-site]/item-code-request` |
| Doctype List | Search "Item Code Request" in desk |
| Workflow Config | Workflow List → Item Code Request Workflow |
| Web Form Config | Web Form List → Item Code Request Form |

## 🔧 Key Files

```
apps/vaaman/vaaman/
├── modules.txt (added Store Management)
├── hooks.py (fixtures & doc_events)
├── fixtures/
│   ├── workflow.json
│   └── workflow_state.json
└── store_management/
    ├── doctype/item_code_request/
    │   ├── item_code_request.json
    │   ├── item_code_request.py
    │   └── item_code_request.js
    └── web_form/item_code_request_form/
        └── item_code_request_form.json
```

## 🎯 Item Mapping (Auto-creation)

| Item Field | Source Field |
|-----------|--------------|
| Item Code | Generated Code |
| Item Name | Item Name |
| Item Group | Item Group |
| Description | Description |
| GST HSN Code | HSN Code |
| Is Stock Item | Is Stock Item |
| Is Fixed Asset | Is Asset Item |
| Asset Category | Asset Category |

## 🐛 Common Issues & Quick Fixes

### Issue: Doctype not found
```bash
bench --site [your-site] migrate
bench clear-cache && bench restart
```

### Issue: Workflow not working
- Check: Workflow List → Item Code Request Workflow → "Is Active" ✓
- Check: User has correct role assigned

### Issue: Web form not accessible
- Check: Web Form List → Item Code Request Form → "Published" ✓
- Run: `bench clear-cache && bench restart`

### Issue: Generated Code is read-only
- ✅ Must be Codification User
- ✅ Document must be in "Pending Codification" state

### Issue: Item not auto-created
- Check: Generated Code field is filled
- Check: Workflow state is "Approved"
- Check: Error logs: `bench --site [your-site] logs`
- Check: Item doesn't already exist with same code

## 📊 Testing Checklist

- [ ] 1. Create request as Store User via web form
- [ ] 2. Verify workflow state: "Pending Codification"
- [ ] 3. Login as Codification User
- [ ] 4. Add Generated Code: TEST-ITEM-001
- [ ] 5. Click "Add Code" action
- [ ] 6. Verify workflow state: "Pending Approval"
- [ ] 7. Login as Item Manager
- [ ] 8. Click "Approve" action
- [ ] 9. Verify success message
- [ ] 10. Check Item List for TEST-ITEM-001
- [ ] 11. Verify all fields are correctly mapped

## 🔍 Debugging Commands

```bash
# View logs
bench --site [your-site] logs

# Check if doctype exists
bench --site [your-site] console
import frappe; print(frappe.db.exists("DocType", "Item Code Request"))

# Check workflow status
import frappe; print(frappe.get_doc("Workflow", "Item Code Request Workflow").is_active)

# Check web form status
import frappe; print(frappe.get_doc("Web Form", "Item Code Request Form").published)

# List all Item Code Requests
import frappe; print(frappe.get_all("Item Code Request", fields=["name", "workflow_state"]))
```

## 📞 Support

| Resource | Location |
|----------|----------|
| Full Documentation | `ITEM_CODE_REQUEST_README.md` |
| Installation Guide | `INSTALLATION_GUIDE.md` |
| Implementation Details | `IMPLEMENTATION_SUMMARY.md` |
| Setup Script | `setup_item_code_request.py` |
| Email | ptpratul2@gmail.com |

## 🎓 User Guide Summary

### For Store Users
1. Visit: `/item-code-request`
2. Fill form and submit
3. Wait for approval notification
4. Check status in Item Code Request list

### For Codification Users
1. Go to: Item Code Request list
2. Filter: Workflow State = "Pending Codification"
3. Open request
4. Add Generated Code
5. Click "Add Code" button

### For Item Managers
1. Go to: Item Code Request list
2. Filter: Workflow State = "Pending Approval"
3. Open request
4. Review details
5. Click "Approve" or "Reject"
6. Item auto-created on approval

## 🔐 Security Notes

- ✅ Role-based access control
- ✅ Document-level permissions
- ✅ Field-level read-only controls
- ✅ Workflow state-based editing
- ✅ Audit trail (track changes enabled)
- ✅ Duplicate prevention

## 📈 Auto-naming Pattern

```
Format: ITMREQ-.#####
Examples:
  ITMREQ-00001
  ITMREQ-00002
  ITMREQ-00003
  ...
```

## ⚙️ Configuration Options

### Enable Email Notifications
Workflow List → Item Code Request Workflow → Check "Send Email Alert"

### Customize Fields
Enable Developer Mode → DocType List → Item Code Request → Edit

### Modify Workflow
Workflow List → Item Code Request Workflow → Edit States/Transitions

### Customize Web Form
Web Form List → Item Code Request Form → Edit

---

**Version:** 1.0  
**Last Updated:** October 30, 2024  
**App:** vaaman  
**Module:** Store Management

