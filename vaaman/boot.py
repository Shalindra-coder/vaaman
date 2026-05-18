# Copyright (c) 2026, Vaaman and contributors


def apply_overrides():
	"""Re-apply monkey patches (safe to call on every request)."""
	try:
		from vaaman.overrides.asset_depreciation import patch_asset_depreciation
		from vaaman.vaaman.rfq_override import patch_rfq

		patch_asset_depreciation()
		patch_rfq()
	except Exception:
		import frappe

		frappe.log_error(title="Vaaman: apply_overrides failed")
