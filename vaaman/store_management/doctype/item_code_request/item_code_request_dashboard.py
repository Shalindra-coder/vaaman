# -*- coding: utf-8 -*-
# Copyright (c) 2024, Your Company
# For license information, please see license.txt

from frappe import _

def get_data():
	return {
		'fieldname': 'name',
		'transactions': [
			{
				'label': _('Request Progress'),
				'items': ['Item Requests by Status', 'Items Created vs Pending']
			},
			{
				'label': _('Request Distribution'),
				'items': ['Requests by Department', 'Requests by Cost Center']
			},
			{
				'label': _('Time Trend'),
				'items': ['Item Requests Over Time']
			}
		]
	}



