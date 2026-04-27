import frappe
from frappe.utils import flt
from frappe.model.document import Document


@frappe.whitelist()
def update_status_db(docname=None, method=None):
	"""
	Updates the custom_status of a single Payment Request.
	Handles both doc object and docname string safely.
	"""
	try:
		# Handle both doc object & string
		if isinstance(docname, Document):
			doc = docname
			docname = doc.name
		else:
			doc = frappe.get_doc("Payment Request", docname)

		doc.reload()

		# Determine new status
		if doc.docstatus == 2:
			new_status = "Cancelled"

		elif not doc.custom_status or doc.workflow_state == "Draft":
			new_status = "Draft"

		elif doc.workflow_state == "Approval Pending By Management":
			new_status = "Ready to Pay"

		elif doc.docstatus == 1:
			new_status = get_payment_request_status(doc)

		elif doc.workflow_state == "Approved":
			new_status = "Initiated"

		else:
			new_status = "Draft"

		# Update only if changed
		if doc.custom_status != new_status:
			doc.db_set("custom_status", new_status, update_modified=False)

			frappe.logger().info(
				f"Updated Payment Request {docname} custom_status to {new_status}"
			)

			# Realtime UI update
			frappe.publish_realtime(
				"payment_request_status_update",
				{"payment_request": docname, "new_status": new_status},
				user="*",
			)

		return new_status

	except Exception as e:
		frappe.log_error(
			f"update_status_db error for {docname}: {e!s}",
			"Payment Request Sync Error"
		)
		raise


def get_payment_request_status(doc):
	"""
	Determines Payment Request status.
	Uses ERPNext's computed status when available, then falls back to amount logic.
	"""
	try:
		core_status = (doc.status or "").strip()
		if core_status in {"Paid", "Partially Paid", "Cancelled", "Failed", "Payment Ordered"}:
			return core_status
		if core_status in {"Requested", "Initiated"}:
			return "Initiated"
		if core_status == "Draft":
			return "Draft"

		amount = flt(doc.grand_total or 0)
		outstanding = flt(doc.outstanding_amount or 0)

		if amount == 0:
			return "Initiated"

		if outstanding == 0:
			return "Paid"

		elif 0 < outstanding < amount:
			return "Partially Paid"

		elif outstanding >= amount:
			return "Initiated"

		else:
			return "Initiated"

	except Exception as e:
		frappe.log_error(
			f"get_payment_request_status error for {doc.name}: {e!s}",
			"Payment Request Sync Error"
		)
		return "Initiated"


@frappe.whitelist()
def update_all_linked_payment_requests(doc, method=None):
	"""
	Triggered on Payment Entry submit/cancel.
	Updates all linked Payment Requests immediately.
	"""
	try:
		references = doc.get("references", [])

		if not references or not isinstance(references, list):
			frappe.log_error(
				f"Invalid references in {doc.doctype} {doc.name}: {references}",
				"Payment Request Sync Error"
			)
			return

		pr_names = set()

		for ref in references:
			reference_doctype = ref.get("reference_doctype")
			reference_name = ref.get("reference_name")
			allocated_amount = flt(ref.get("allocated_amount", 0))

			if reference_doctype and reference_name and allocated_amount > 0:

				payment_requests = frappe.get_all(
					"Payment Request",
					filters={
						"reference_doctype": reference_doctype,
						"reference_name": reference_name,
						"docstatus": 1,
					},
					pluck="name",
				)

				for pr_name in payment_requests:
					pr_names.add(pr_name)

		for pr_name in pr_names:
			update_status_db(docname=pr_name)

	except Exception as e:
		frappe.log_error(
			f"update_all_linked_payment_requests error in {doc.name}: {e!s}",
			"Payment Request Sync Error"
		)


# ➤ ERPNext core wrapper (override)
from erpnext.accounts.doctype.payment_request.payment_request import (
	update_payment_requests_as_per_pe_references as original_update,
)


def custom_update_payment_requests(references, cancel=None):
	"""
	Wrapper over ERPNext core function.
	Ensures correct references handling.
	"""
	try:
		# If Payment Entry doc passed
		if isinstance(references, Document) and references.doctype == "Payment Entry":
			references = references.get("references", [])
			frappe.logger().info(f"Extracted references: {references}")

		if not references or not isinstance(references, list):
			frappe.log_error(
				f"Invalid references in custom_update_payment_requests: {references}",
				"Payment Request Sync Error",
			)
			return

		return original_update(references, cancel)

	except Exception as e:
		frappe.log_error(
			f"custom_update_payment_requests error: {e!s}",
			"Payment Request Sync Error"
		)


def sync_all_payment_requests():
	"""
	Fallback: Sync all submitted Payment Requests.
	"""
	try:
		pr_names = frappe.get_all(
			"Payment Request",
			filters={"docstatus": 1},
			pluck="name"
		)

		for name in pr_names:
			frappe.enqueue(
				"vaaman.payment_request.update_status_db",
				docname=name
			)

	except Exception as e:
		frappe.log_error(
			f"sync_all_payment_requests error: {e!s}",
			"Payment Request Sync Error"
		)


@frappe.whitelist()
def resync_existing_payment_requests(only_submitted=1):
	"""
	One-time/manual utility to resync custom_status for existing Payment Requests.

	Args:
	        only_submitted (int|str|bool): 1/true -> only docstatus=1, else all.
	Returns:
	        dict: processed/updated/errors counters.
	"""
	try:
		if isinstance(only_submitted, str):
			only_submitted = only_submitted.strip().lower() in {"1", "true", "yes"}
		else:
			only_submitted = bool(only_submitted)

		filters = {"docstatus": 1} if only_submitted else {}
		pr_names = frappe.get_all("Payment Request", filters=filters, pluck="name")

		processed = 0
		updated = 0
		errors = 0

		for pr_name in pr_names:
			try:
				processed += 1
				doc = frappe.get_doc("Payment Request", pr_name)
				old_status = doc.custom_status
				new_status = update_status_db(docname=pr_name)
				if new_status != old_status:
					updated += 1
			except Exception:
				errors += 1
				frappe.log_error(
					f"resync_existing_payment_requests failed for {pr_name}",
					"Payment Request Sync Error",
				)

		frappe.db.commit()
		return {"processed": processed, "updated": updated, "errors": errors}

	except Exception as e:
		frappe.log_error(
			f"resync_existing_payment_requests error: {e!s}",
			"Payment Request Sync Error"
		)
		raise
