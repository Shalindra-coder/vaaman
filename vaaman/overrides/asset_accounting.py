# Copyright (c) 2026, Vaaman and contributors
# Shared asset depreciation / disposal accounting helpers.

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, get_link_to_form

DISPOSAL_DATE_FLAG = "vaaman_disposal_as_on_date"


def set_disposal_as_on_date(date):
	"""Context for disposal GL while Sales Invoice is submitting."""
	if date:
		frappe.flags[DISPOSAL_DATE_FLAG] = getdate(date)
	else:
		frappe.flags.pop(DISPOSAL_DATE_FLAG, None)


def get_disposal_as_on_date(asset):
	return (
		getattr(frappe.flags, DISPOSAL_DATE_FLAG, None)
		or asset.disposal_date
		or None
	)


def get_active_depreciation_schedule_name(asset_name, finance_book=None):
	filters = {"asset": asset_name, "status": "Active"}
	if finance_book:
		filters["finance_book"] = finance_book
		name = frappe.db.get_value("Asset Depreciation Schedule", filters, "name")
		if name:
			return name
	return frappe.db.get_value(
		"Asset Depreciation Schedule", {"asset": asset_name, "status": "Active"}, "name"
	)


def get_accumulated_depreciation_from_schedule(asset_name, finance_book=None, as_on_date=None):
	"""Accumulated depreciation from schedule rows on or before the disposal date only."""
	schedule_name = get_active_depreciation_schedule_name(asset_name, finance_book)
	if not schedule_name:
		return None

	if not as_on_date:
		return None

	as_on_date = getdate(as_on_date)

	# Pro-rata row is stored on the actual disposal date.
	exact = frappe.db.get_value(
		"Depreciation Schedule",
		{"parent": schedule_name, "schedule_date": as_on_date},
		"accumulated_depreciation_amount",
	)
	if exact is not None:
		return flt(exact)

	return frappe.db.get_value(
		"Depreciation Schedule",
		{"parent": schedule_name, "schedule_date": ["<=", as_on_date]},
		"accumulated_depreciation_amount",
		order_by="schedule_date desc",
	)


def get_salvage_value(asset, finance_book=None):
	if not asset.finance_books:
		return 0
	if finance_book:
		for row in asset.finance_books:
			if row.finance_book == finance_book:
				return flt(row.expected_value_after_useful_life)
	return flt(asset.finance_books[0].expected_value_after_useful_life)


def get_authoritative_wdv(asset, finance_book=None, as_on_date=None):
	"""WDV for disposal GL. Never use future schedule rows beyond the disposal date."""
	as_on_date = getdate(as_on_date or get_disposal_as_on_date(asset))

	if as_on_date:
		accum = get_accumulated_depreciation_from_schedule(asset.name, finance_book, as_on_date)
		if accum is not None:
			wdv = flt(
				flt(asset.gross_purchase_amount) - flt(accum),
				asset.precision("gross_purchase_amount"),
			)
			salvage = get_salvage_value(asset, finance_book)
			return max(wdv, salvage)

	return flt(asset.get_value_after_depreciation(finance_book))


def apply_wdv_on_asset(asset, wdv, finance_book=None):
	idx = 0
	if finance_book:
		for row in asset.finance_books:
			if row.finance_book == finance_book:
				idx = row.idx - 1
				break
	if asset.finance_books:
		asset.finance_books[idx].value_after_depreciation = wdv


def submit_draft_depreciation_je(je_name):
	je = frappe.get_doc("Journal Entry", je_name)
	if je.docstatus != 0 or je.voucher_type != "Depreciation Entry":
		return False

	je.flags.planned_depr_entry = True
	je.flags.ignore_permissions = True
	je.submit()
	return True


def submit_draft_depreciation_jes_for_asset(asset_name):
	schedule_name = get_active_depreciation_schedule_name(asset_name)
	if not schedule_name:
		return

	je_names = frappe.get_all(
		"Depreciation Schedule",
		filters={"parent": schedule_name, "journal_entry": ["is", "set"]},
		pluck="journal_entry",
	)
	for je_name in set(je_names):
		if frappe.db.get_value("Journal Entry", je_name, "docstatus") == 0:
			submit_draft_depreciation_je(je_name)


def sync_finance_book_after_depreciation_submit(asset, asset_depr_schedule_doc, depr_schedule):
	"""Update finance book the same way ERPNext does when workflow is absent."""
	asset.reload()
	idx = cint(asset_depr_schedule_doc.finance_book_id) - 1
	if idx < 0 or idx >= len(asset.finance_books):
		idx = 0
	row = asset.finance_books[idx]
	row.value_after_depreciation -= flt(depr_schedule.depreciation_amount)
	row.db_update()


def _finance_book_row(asset, finance_book=None):
	if not asset.finance_books:
		return None, -1
	if finance_book:
		for i, row in enumerate(asset.finance_books):
			if row.finance_book == finance_book:
				return row, i
	return asset.finance_books[0], 0


def ensure_disposal_depreciation(asset_name, disposal_date, notes=None):
	"""Create pro-rata schedule row + depreciation JE when SI submit skipped depreciate_asset."""
	disposal_date = getdate(disposal_date)
	schedule_name = get_active_depreciation_schedule_name(asset_name)
	if schedule_name and frappe.db.exists(
		"Depreciation Schedule",
		{"parent": schedule_name, "schedule_date": disposal_date},
	):
		return

	asset = frappe.get_doc("Asset", asset_name)
	if not asset.calculate_depreciation or asset.status == "Fully Depreciated":
		return

	from erpnext.assets.doctype.asset.depreciation import depreciate_asset

	asset.flags.ignore_validate_update_after_submit = True
	depreciate_asset(
		asset,
		disposal_date,
		notes or _("Depreciation for asset disposal on {0}").format(disposal_date),
	)


def finalize_asset_after_sale(asset_name, disposal_date=None, finance_book=None):
	asset = frappe.get_doc("Asset", asset_name)
	wdv = get_authoritative_wdv(asset, finance_book, disposal_date)
	row, _idx = _finance_book_row(asset, finance_book)
	if row:
		row.value_after_depreciation = wdv
		row.db_update()

	updates = {"status": "Sold"}
	if disposal_date:
		updates["disposal_date"] = disposal_date
	asset.db_set(updates)


def sync_depreciation_schedule_je_links(asset_name):
	"""Clear schedule links to cancelled, missing, or deleted journal entries."""
	schedule_name = get_active_depreciation_schedule_name(asset_name)
	if not schedule_name:
		return False

	changed = False
	for row in frappe.get_all(
		"Depreciation Schedule",
		filters={"parent": schedule_name},
		fields=["name", "journal_entry"],
	):
		if not row.journal_entry:
			continue
		if not frappe.db.exists("Journal Entry", row.journal_entry):
			frappe.db.set_value("Depreciation Schedule", row.name, "journal_entry", None)
			changed = True
			continue
		if cint(frappe.db.get_value("Journal Entry", row.journal_entry, "docstatus")) == 2:
			frappe.db.set_value("Depreciation Schedule", row.name, "journal_entry", None)
			changed = True
	return changed


def rebuild_depreciation_schedule_after_si_cancel(asset_name, sales_invoice):
	"""Restore full depreciation schedule after asset sale invoice is cancelled."""
	from erpnext.assets.doctype.asset_depreciation_schedule.asset_depreciation_schedule import (
		make_new_active_asset_depr_schedules_and_cancel_current_ones,
	)

	asset = frappe.get_doc("Asset", asset_name)
	if not asset.calculate_depreciation:
		return

	sync_depreciation_schedule_je_links(asset_name)

	note = _("Schedule restored after Sales Invoice {0} was cancelled.").format(
		get_link_to_form("Sales Invoice", sales_invoice)
	)
	asset.flags.ignore_validate_update_after_submit = True
	make_new_active_asset_depr_schedules_and_cancel_current_ones(
		asset, note, date_of_return=getdate()
	)
	asset.reload()

	row, _idx = _finance_book_row(asset)
	if row:
		schedule_name = get_active_depreciation_schedule_name(asset_name, row.finance_book)
		last_booked_accum = frappe.db.get_value(
			"Depreciation Schedule",
			{"parent": schedule_name, "journal_entry": ["is", "set"]},
			"accumulated_depreciation_amount",
			order_by="schedule_date desc",
		)
		if last_booked_accum is not None:
			row.value_after_depreciation = flt(asset.gross_purchase_amount) - flt(last_booked_accum)
			row.db_update()

	asset.db_set("disposal_date", None)
	asset.set_status()


def on_depreciation_je_cancel_or_trash(doc, method=None):
	"""Clear schedule links when a depreciation journal entry is cancelled or deleted."""
	if doc.voucher_type != "Depreciation Entry":
		return

	for row_name in frappe.get_all(
		"Depreciation Schedule", filters={"journal_entry": doc.name}, pluck="name"
	):
		frappe.db.set_value("Depreciation Schedule", row_name, "journal_entry", None)
