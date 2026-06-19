# Copyright (c) 2026, Vaaman and contributors
# Asset sale: submit pro-rata depreciation before disposal GL; WDV as at disposal date only.

import frappe
from frappe import _
from frappe.utils import flt

from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from erpnext.assets.doctype.asset.depreciation import (
	get_gl_entries_on_asset_disposal,
	get_gl_entries_on_asset_regain,
)

from vaaman.overrides.asset_accounting import (
	apply_wdv_on_asset,
	ensure_disposal_depreciation,
	finalize_asset_after_sale,
	get_authoritative_wdv,
	get_salvage_value,
	rebuild_depreciation_schedule_after_si_cancel,
	set_disposal_as_on_date,
	submit_draft_depreciation_jes_for_asset,
)


class CustomSalesInvoice(SalesInvoice):
	def process_asset_depreciation(self):
		super().process_asset_depreciation()
		if self.is_internal_transfer():
			return
		if self.docstatus == 2 and not self.is_return:
			for row in self.get("items"):
				if row.asset:
					rebuild_depreciation_schedule_after_si_cancel(row.asset, self.name)
			return
		if (self.is_return and self.docstatus == 2) or (not self.is_return and self.docstatus == 1):
			disposal_date = self.get_disposal_date()
			for row in self.get("items"):
				if row.asset:
					finalize_asset_after_sale(row.asset, disposal_date, row.finance_book)

	def get_gl_entries_for_fixed_asset(self, item, gl_entries):
		if not item.asset:
			return

		# make_gl_entries_on_cancel() still calls get_gl_entries() to build rows for reversal.
		# restore_asset() already reversed pro-rata depreciation — do not post it again here.
		if self.docstatus == 2 and not self.is_return:
			return super().get_gl_entries_for_fixed_asset(item, gl_entries)

		disposal_date = self.get_disposal_date() if not self.is_return else None

		try:
			set_disposal_as_on_date(disposal_date)

			if not self.is_return and self.docstatus == 1:
				ensure_disposal_depreciation(
					item.asset, disposal_date, self.get_note_for_asset_sale(frappe.get_doc("Asset", item.asset))
				)
				submit_draft_depreciation_jes_for_asset(item.asset)

			frappe.clear_document_cache("Asset", item.asset)
			asset = frappe.get_doc("Asset", item.asset)

			if not self.is_return and self.docstatus == 1 and asset.calculate_depreciation:
				wdv = get_authoritative_wdv(asset, item.finance_book, disposal_date)
				salvage = get_salvage_value(asset, item.finance_book)
				# Fully Depreciated assets legitimately have WDV at salvage; no pro-rata is needed.
				if asset.status != "Fully Depreciated" and flt(wdv) <= flt(salvage) + 0.01:
					frappe.throw(
						_(
							"Asset {0}: written down value ({1}) equals salvage ({2}). "
							"Pro-rata depreciation for {3} was not posted — cancel this invoice, "
							"ensure depreciation entries are submitted, and submit again."
						).format(item.asset, wdv, salvage, disposal_date)
					)
				apply_wdv_on_asset(asset, wdv, item.finance_book)

			if self.is_return:
				fixed_asset_gl_entries = get_gl_entries_on_asset_regain(
					asset,
					item.base_net_amount,
					item.finance_book,
					self.get("doctype"),
					self.get("name"),
					self.get("posting_date"),
				)
			else:
				fixed_asset_gl_entries = get_gl_entries_on_asset_disposal(
					asset,
					item.base_net_amount,
					item.finance_book,
					self.get("doctype"),
					self.get("name"),
					self.get("posting_date"),
				)

			for gle in fixed_asset_gl_entries:
				gle["against"] = self.customer
				gl_entries.append(self.get_gl_dict(gle, item=item))
		finally:
			set_disposal_as_on_date(None)
