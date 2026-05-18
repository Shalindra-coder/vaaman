# Copyright (c) 2026, Vaaman and contributors
# ERPNext skips submit on planned depreciation JEs when Journal Entry has workflow.
# Disposal GL on Sales Invoice runs in the same transaction before approval, so WDV is stale.

import importlib

import frappe

from frappe.utils import flt

from vaaman.overrides.asset_accounting import (
	get_authoritative_wdv,
	get_disposal_as_on_date,
	submit_draft_depreciation_je,
	sync_finance_book_after_depreciation_submit,
)

DEPRECIATION_MODULE = "erpnext.assets.doctype.asset.depreciation"


def patch_asset_depreciation():
	module = importlib.import_module(DEPRECIATION_MODULE)
	if getattr(module, "_vaaman_patched", False):
		return

	_patch_get_asset_details(module)
	original = module._make_journal_entry_for_depreciation

	def _make_journal_entry_for_depreciation(
		asset_depr_schedule_doc,
		asset,
		date,
		depr_schedule,
		sch_start_idx,
		sch_end_idx,
		depreciation_cost_center,
		depreciation_series,
		credit_account,
		debit_account,
		accounting_dimensions,
	):
		je_name_before = depr_schedule.journal_entry
		original(
			asset_depr_schedule_doc,
			asset,
			date,
			depr_schedule,
			sch_start_idx,
			sch_end_idx,
			depreciation_cost_center,
			depreciation_series,
			credit_account,
			debit_account,
			accounting_dimensions,
		)
		_submit_planned_depreciation_je(
			asset_depr_schedule_doc, asset, depr_schedule, je_name_before
		)

	module._make_journal_entry_for_depreciation = _make_journal_entry_for_depreciation
	module._vaaman_patched = True


def _patch_get_asset_details(module):
	original = module.get_asset_details

	def get_asset_details(asset, finance_book=None):
		as_on_date = get_disposal_as_on_date(asset)
		value_after_depreciation = get_authoritative_wdv(asset, finance_book, as_on_date)
		accumulated_depr_amount = flt(asset.gross_purchase_amount) - flt(value_after_depreciation)

		fixed_asset_account, accumulated_depr_account, _ = module.get_depreciation_accounts(
			asset.asset_category, asset.company
		)
		disposal_account, depreciation_cost_center = module.get_disposal_account_and_cost_center(
			asset.company
		)
		depreciation_cost_center = asset.cost_center or depreciation_cost_center

		return (
			fixed_asset_account,
			asset,
			depreciation_cost_center,
			accumulated_depr_account,
			accumulated_depr_amount,
			disposal_account,
			value_after_depreciation,
		)

	module.get_asset_details = get_asset_details


def _submit_planned_depreciation_je(asset_depr_schedule_doc, asset, depr_schedule, je_name_before):
	if not depr_schedule.journal_entry:
		return

	if (
		depr_schedule.journal_entry == je_name_before
		and frappe.db.get_value("Journal Entry", depr_schedule.journal_entry, "docstatus") != 0
	):
		return

	try:
		if submit_draft_depreciation_je(depr_schedule.journal_entry):
			sync_finance_book_after_depreciation_submit(
				asset, asset_depr_schedule_doc, depr_schedule
			)
	except Exception:
		frappe.log_error(
			title="Vaaman: planned depreciation submit failed",
			message=frappe.get_traceback(),
		)
		raise
