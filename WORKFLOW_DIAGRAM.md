# Item Code Request Workflow - Visual Diagram

## Complete Workflow Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ITEM CODE REQUEST WORKFLOW                        │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│  Store User  │
│              │
│  Creates     │
│  Request     │
└──────┬───────┘
       │
       │ (Fills form via web form or desk)
       │ - Item Name
       │ - HSN Code
       │ - Item Group
       │ - Description
       │ - Is Stock Item / Is Asset Item
       │
       ▼
┌──────────────────┐
│                  │
│   STATE: DRAFT   │
│                  │
│   (doc_status=0) │
│                  │
└──────┬───────────┘
       │
       │ Action: "Submit"
       │ (Store User clicks Submit)
       │
       ▼
┌───────────────────────────┐
│                           │
│  STATE: PENDING           │
│  CODIFICATION             │
│                           │
│  (doc_status=1)           │
│                           │
│  Waiting for item code    │
│  assignment               │
│                           │
└───────────┬───────────────┘
            │
            │ Codification User:
            │ - Opens request
            │ - Fills "Generated Code" field
            │   (e.g., PROD-2024-001)
            │
            ▼
┌───────────────────────────┐
│                           │
│  Codification User fills  │
│  Generated Code field     │
│                           │
│  Example: PROD-2024-001   │
│                           │
└───────────┬───────────────┘
            │
            │ Action: "Add Code"
            │ (Codification User clicks Add Code)
            │ Validates: Generated Code is not empty
            │
            ▼
┌───────────────────────────┐
│                           │
│  STATE: PENDING APPROVAL  │
│                           │
│  (doc_status=1)           │
│                           │
│  Waiting for manager      │
│  approval                 │
│                           │
└───────────┬───────────────┘
            │
            │ Item Manager:
            │ - Reviews request
            │ - Reviews generated code
            │ - Decides to approve or reject
            │
            ├────────────────┬──────────────┐
            │                │              │
    Action: "Approve"    Action: "Reject"  │
            │                │              │
            ▼                ▼              │
┌──────────────────┐  ┌──────────────────┐│
│                  │  │                  ││
│ STATE: APPROVED  │  │  STATE: REJECTED ││
│                  │  │                  ││
│ (doc_status=1)   │  │  (doc_status=2)  ││
│                  │  │                  ││
│ ✓ Final State    │  │  ✗ Final State   ││
│                  │  │                  ││
└────────┬─────────┘  └──────────────────┘│
         │                                 │
         │ Automatic Process:              │
         │ - System detects workflow       │
         │   state = "Approved"            │
         │ - Triggers on_update_after_     │
         │   submit() method               │
         │ - Calls create_item()           │
         │                                 │
         ▼                                 │
┌──────────────────────────┐              │
│                          │              │
│  CREATE ITEM IN ERPNEXT  │              │
│                          │              │
│  - Item Code ← Generated │              │
│    Code                  │              │
│  - Item Name ← Item Name │              │
│  - Item Group ← Item     │              │
│    Group                 │              │
│  - HSN Code ← HSN Code   │              │
│  - Is Stock Item ← Is    │              │
│    Stock Item            │              │
│  - Is Fixed Asset ← Is   │              │
│    Asset Item            │              │
│  - Asset Category ← Asset│              │
│    Category              │              │
│                          │              │
└────────┬─────────────────┘              │
         │                                 │
         │ Success Message:                │
         │ "Item {Generated Code} created  │
         │  successfully in ERPNext"       │
         │                                 │
         ▼                                 │
┌──────────────────────────┐              │
│                          │              │
│   ITEM CREATED IN        │              │
│   ERPNEXT                │              │
│                          │              │
│   ✓ Ready to use         │              │
│                          │              │
└──────────────────────────┘              │
                                          │
                                          │
            ┌─────────────────────────────┘
            │
            │ End State: Rejected
            │ - Item NOT created
            │ - Request can be reviewed
            │   or resubmitted (new request)
            │
            ▼
┌──────────────────────────┐
│                          │
│   REQUEST REJECTED       │
│                          │
│   ✗ Item not created     │
│   ✗ Request closed       │
│                          │
└──────────────────────────┘
```

## Role-Based View

### Store User Perspective
```
┌─────────────────────────────────────────┐
│ 1. Access web form                      │
│    URL: /item-code-request              │
├─────────────────────────────────────────┤
│ 2. Fill required information:           │
│    • Item Name                          │
│    • HSN Code                           │
│    • Item Group                         │
│    • Description (optional)             │
│    • Is Stock Item?                     │
│    • Is Asset Item?                     │
│    • Asset Category (if asset)          │
├─────────────────────────────────────────┤
│ 3. Submit request                       │
│    → Request ID generated (ITMREQ-####) │
├─────────────────────────────────────────┤
│ 4. Wait for approval                    │
│    • Can view own requests in list      │
│    • Can track status                   │
├─────────────────────────────────────────┤
│ 5. Receive notification (if enabled)    │
│    • When code is assigned              │
│    • When request is approved/rejected  │
└─────────────────────────────────────────┘
```

### Codification User Perspective
```
┌─────────────────────────────────────────┐
│ 1. Check pending requests               │
│    Filter: Workflow State =             │
│            "Pending Codification"       │
├─────────────────────────────────────────┤
│ 2. Open request to review               │
│    • View item details                  │
│    • Review item group                  │
│    • Understand item type               │
├─────────────────────────────────────────┤
│ 3. Generate/Assign item code            │
│    • Follow company naming convention   │
│    • Enter in "Generated Code" field    │
│    • Examples:                          │
│      - PROD-2024-001                    │
│      - ITM-ELEC-123                     │
│      - RAW-MAT-456                      │
├─────────────────────────────────────────┤
│ 4. Click "Add Code" action              │
│    → Request moves to Pending Approval  │
└─────────────────────────────────────────┘
```

### Item Manager Perspective
```
┌─────────────────────────────────────────┐
│ 1. Check pending approvals              │
│    Filter: Workflow State =             │
│            "Pending Approval"           │
├─────────────────────────────────────────┤
│ 2. Open request to review               │
│    • Verify item details                │
│    • Check generated code               │
│    • Review item classification         │
│    • Confirm HSN code                   │
├─────────────────────────────────────────┤
│ 3. Make decision                        │
│    ┌──────────────────┬───────────────┐ │
│    │   Approve        │   Reject      │ │
│    ├──────────────────┼───────────────┤ │
│    │ • All details OK │ • Missing info│ │
│    │ • Code is valid  │ • Wrong code  │ │
│    │ • Click "Approve"│ • Wrong group │ │
│    │                  │ • Click       │ │
│    │                  │   "Reject"    │ │
│    └──────────────────┴───────────────┘ │
├─────────────────────────────────────────┤
│ 4. If Approved:                         │
│    • Item automatically created         │
│    • Success message appears            │
│    • Can view created item              │
│                                         │
│    If Rejected:                         │
│    • Request closed                     │
│    • Store user can create new request │
└─────────────────────────────────────────┘
```

## State Transition Matrix

| Current State | Available Actions | Next State | Role Required | Conditions |
|---------------|-------------------|------------|---------------|------------|
| Draft | Submit | Pending Codification | Store User | All required fields filled |
| Pending Codification | Add Code | Pending Approval | Codification User | Generated Code is not empty |
| Pending Approval | Approve | Approved | Item Manager | - |
| Pending Approval | Reject | Rejected | Item Manager | - |
| Approved | - | - | - | Final state |
| Rejected | - | - | - | Final state |

## Document Status (docstatus) Mapping

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  docstatus = 0 (Draft)                                      │
│  ├─ State: Draft                                            │
│  └─ Editable by: Store User (creator)                       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  docstatus = 1 (Submitted)                                  │
│  ├─ State: Pending Codification                             │
│  │  └─ Editable by: Codification User                       │
│  ├─ State: Pending Approval                                 │
│  │  └─ Editable by: Item Manager                            │
│  └─ State: Approved                                         │
│     └─ Editable by: None (final state)                      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  docstatus = 2 (Cancelled)                                  │
│  └─ State: Rejected                                         │
│     └─ Editable by: None (final state)                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Automatic Item Creation Process

```
┌─────────────────────────────────────────────────────────────┐
│         WORKFLOW STATE CHANGES TO "APPROVED"                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Trigger Event:      │
              │  on_update_after_    │
              │  submit()            │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Check:              │
              │  workflow_state ==   │
              │  "Approved"?         │
              └──────────┬───────────┘
                         │
                    Yes  │  No → Exit
                         │
                         ▼
              ┌──────────────────────┐
              │  Check:              │
              │  Generated Code      │
              │  exists?             │
              └──────────┬───────────┘
                         │
                    Yes  │  No → Error
                         │
                         ▼
              ┌──────────────────────┐
              │  Check:              │
              │  Item already        │
              │  exists?             │
              └──────────┬───────────┘
                         │
                    No   │  Yes → Skip
                         │
                         ▼
              ┌──────────────────────┐
              │  Create Item Doc:    │
              │  frappe.get_doc({    │
              │    "doctype": "Item",│
              │    ...fields...      │
              │  })                  │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Insert Item:        │
              │  item.insert(        │
              │    ignore_permissions│
              │    =True             │
              │  )                   │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Success!            │
              │  - Show message      │
              │  - Add comment       │
              │  - Log success       │
              └──────────────────────┘
```

## Field Dependencies

```
┌────────────────────────────────────────┐
│  Is Asset Item (Checkbox)              │
└──────────────┬─────────────────────────┘
               │
               │ if checked (value = 1)
               │
               ▼
┌────────────────────────────────────────┐
│  Asset Category (Link)                 │
│  - Becomes visible                     │
│  - Becomes required                    │
│  - Must select valid Asset Category    │
└────────────────────────────────────────┘
```

## Permission Matrix

| Role | Create | Read | Write | Submit | Cancel | Approve | Delete |
|------|--------|------|-------|--------|--------|---------|--------|
| Store User | ✓ | ✓ (own) | ✓ (own) | - | - | - | ✓ (own) |
| Codification User | - | ✓ (all) | ✓ (all) | - | - | - | - |
| Item Manager | - | ✓ (all) | ✓ (all) | ✓ | ✓ | ✓ | - |

## Error Handling Flow

```
If error during item creation:
    │
    ├─ frappe.log_error()
    │  └─ Creates Error Log document
    │     └─ Viewable by System Manager
    │
    ├─ frappe.throw()
    │  └─ Shows error to user
    │     └─ Transaction rolled back
    │
    └─ Item Code Request remains in
       "Approved" state but item not created
       └─ Can be retried manually
```

---

**Legend:**
- ▼ : Flow direction
- ✓ : Allowed/Success
- ✗ : Not allowed/Failed
- ├─ : Branch
- └─ : End of branch
- → : Transition

