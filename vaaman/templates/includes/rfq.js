// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

window.doc = {{ doc.as_json() }};

$(document).ready(function() {
	new rfq();
	doc.supplier = "{{ doc.supplier }}";
	doc.currency = "{{ doc.currency }}";
	doc.number_format = "{{ doc.number_format }}";
	doc.buying_price_list = "{{ doc.buying_price_list }}";
});

rfq = class rfq {
	constructor(){
		this.onfocus_select_all();
		this.change_qty();
		this.change_rate();
		this.change_discount();
		this.update_freight_charges();
		this.update_gst();
		this.terms();
		this.payment_terms_on_change();
		this.submit_rfq();
		this.navigate_quotations();
		this.get_final_amount();
		this.calculate_grand_total_with_tax(); // Initialize calculation
	}

	onfocus_select_all(){
		$("input").click(function(){
			$(this).select();
		});
	}

	// update base amount after qty change
	change_qty(){
		var me = this;
		$('.rfq-items').on("change", ".rfq-qty", function(){
			me.idx = parseFloat($(this).attr('data-idx'));
			me.qty = parseFloat(flt($(this).val())) || 0;
			let rate = parseFloat(flt($(repl('.rfq-rate[data-idx=%(idx)s]',{'idx': me.idx})).val())) || 0;

			let amount = rate * me.qty;
			me.set_base_amount(me.idx, amount);

			$(this).val(format_number(me.qty, doc.number_format, 2));
			me.recalculate_item_totals(me.idx);
			me.recalculate_grand_total();
			me.calculate_grand_total_with_tax(); // Update grand total with tax
		});
	}

	change_rate(){
		var me = this;
		$(".rfq-items").on("change", ".rfq-rate", function(){
			me.idx = parseFloat($(this).attr('data-idx'));
			let rate = parseFloat(flt($(this).val())) || 0;
			let qty = parseFloat(flt($(repl('.rfq-qty[data-idx=%(idx)s]',{'idx': me.idx})).val())) || 0;

			let amount = rate * qty;
			me.set_base_amount(me.idx, amount);

			$(this).val(format_number(rate, doc.number_format, 2));
			me.recalculate_item_totals(me.idx);
			me.recalculate_grand_total();
			me.calculate_grand_total_with_tax(); // Update grand total with tax
		});
	}

	change_discount(){
		var me = this;
		$(".rfq-items").on("change", ".rfq-discount", function(){
			me.idx = parseFloat($(this).attr('data-idx'));

			let discount_percent = parseFloat(flt($(this).val())) || 0;
			let qty = parseFloat(flt($(repl('.rfq-qty[data-idx=%(idx)s]', {'idx': me.idx})).val())) || 0;
			let rate = parseFloat(flt($(repl('.rfq-rate[data-idx=%(idx)s]', {'idx': me.idx})).val())) || 0;

			let discounted_rate = rate - (rate * (discount_percent / 100));
			let amount = discounted_rate * qty;

			me.set_base_amount(me.idx, amount);
			me.recalculate_item_totals(me.idx);
			me.recalculate_grand_total();
			me.calculate_grand_total_with_tax(); // Update grand total with tax
		});
	}

	// UPDATED: GST now applies to grand total, not individual items
	update_gst() {
		var me = this;
		$(document).on("change", "#gst_percentage", function () {
			let gst_percentage = parseFloat($(this).val()) || 0;
			doc.gst_percentage = gst_percentage;
			me.calculate_grand_total_with_tax();
		});
	}

	// UPDATED: Freight now applies to grand total, not individual items
	update_freight_charges() {
		var me = this;
		$(document).on("change", "#freight_percentage", function () {
			let freight_percentage = parseFloat($(this).val()) || 0;
			doc.freight_percentage = freight_percentage;
			me.calculate_grand_total_with_tax();
		});
	}

	// SIMPLIFIED: Only calculate base amounts for items (no individual GST/freight)
	recalculate_item_totals(idx){
		let item = doc.items.find(i => i.idx === idx);
		if(!item) return;

		// Only calculate base amount (qty * rate after discount)
		let base_amount = item.base_amount || 0;
		item.final_amount = base_amount; // Final amount is just the base amount now

		// Update display
		this.update_display(idx);
	}

	set_base_amount(idx, amount){
		let item = doc.items.find(i => i.idx === idx);
		if(item){
			item.base_amount = amount;
			item.amount = amount; // Keep original amount field for compatibility
			item.final_amount = amount; // Set final amount to base amount
		}
	}

	update_display(idx){
		let item = doc.items.find(i => i.idx === idx);
		if(!item) return;

		// Show the base amount for each item
		let total = item.base_amount || 0;
		$(repl('.rfq-amount[data-idx=%(idx)s]',{'idx': idx}))
			.text(format_number(total, doc.number_format, 2));
	}

	// UPDATED: Calculate grand total (sum of all item base amounts)
	recalculate_grand_total(){
		doc.grand_total = 0.0;
		doc.items.forEach(function(item){
			// Use base amount for grand total calculation
			let total = item.base_amount || 0;
			doc.grand_total += flt(total);
		});
		$('.tax-grand-total').text(format_number(doc.grand_total, doc.number_format, 2));
	}

	// NEW: Calculate grand total with GST and freight charges applied to the total
	calculate_grand_total_with_tax() {
		let net_total = doc.grand_total || 0;
		let gst_percentage = doc.gst_percentage || 0;
		let freight_percentage = doc.freight_percentage || 0;

		// Calculate GST amount on net total
		let gst_amount = (net_total * gst_percentage) / 100;

		// Calculate freight amount on (net total + GST)
		let total_with_gst = net_total + gst_amount;
		let freight_amount = (total_with_gst * freight_percentage) / 100;

		// Calculate final grand total
		let grand_total_with_tax = total_with_gst + freight_amount;

		// Store values for later use
		doc.gst_amount = gst_amount;
		doc.freight_amount = freight_amount;
		doc.grand_total_with_tax = grand_total_with_tax;

		// Update the display field
		$('#grand_total_with_tax').val(format_number(grand_total_with_tax, doc.number_format, 2));

	}

	terms(){
		$(".terms").on("change", ".terms-feedback", function(){
			doc.terms = $(this).val();
		});
	}

	submit_rfq() {
		$('.btn-sm').click(function () {
			var me = this;

			// 1️⃣ Collect item details
			let item_details = [];
			doc.items.forEach(function (item) {
				let rate = parseFloat(
					$(repl('.rfq-rate[data-idx=%(idx)s]', { 'idx': item.idx })).val().replace(/,/g, '')
				) || 0;
				let qty = parseFloat(item.qty) || 0;
				let discount = parseFloat(
					$(repl('.rfq-discount[data-idx=%(idx)s]', { 'idx': item.idx })).val()
				) || 0;
				let amount = parseFloat(item.base_amount) || 0;

				item_details.push({
					item_name: item.item_name,
					item_code: item.item_code,
					rate: rate,
					qty: qty,
					custom_discount_: discount,
					amount: amount,
					warehouse: item.warehouse
				});
			});

			// 2️⃣ Collect payment term data
			const table = document.getElementById('paymentScheduleTable');
			const rows = table ? table.querySelectorAll('tbody tr') : [];
			let payment_term_data = [];
			rows.forEach(row => {
				const cells = row.querySelectorAll('td');
					payment_term_data.push({
						paymentTerm: cells[0].textContent,
						description: cells[1].textContent,
						dueDate: cells[2].querySelector('input').value,
						percentage: cells[3].textContent,
						amount: cells[4].textContent
					});

			});

			// 3️⃣ Collect all form data
			let gstValue = $('#gst_percentage').val() || 0;
			let freightValue = $('#freight_percentage').val() || 0;
			let payment_terms_template = $('#payment_terms_template option:selected').text();
			let Encoterm = $('#encoterm_template option:selected').text();
			let document_notes = $('#document_notes').val() || '';
			let additional_notes = $('#additional_notes').val() || '';

			// 4️⃣ File handling - Updated to use new field ID
			let fileInput = document.getElementById('document_attachment');
			let file = fileInput ? fileInput.files[0] : null;

			// Function to submit to Frappe
			function submitToFrappe(other_details) {
				frappe.freeze();
				frappe.call({
					type: "POST",
					method: "vaaman.api.create_supplier_quotation",
					args: {
						doc: doc,
						item_details: item_details,
						payment_term_data: payment_term_data,
						other_details: other_details
					},
					btn: me,
					callback: function (r) {
						frappe.unfreeze();
						if (r.message) {
							$('.btn-sm').hide();
							window.location.href = "/supplier-quotations/" + encodeURIComponent(r.message);
						}
					}
				});
			}

			// 5️⃣ Prepare other details with tax calculations
			let other_details = {
				gstValue: gstValue,
				freightValue: freightValue,
				payment_terms_template: payment_terms_template,
				document_notes: document_notes,
				additional_notes: additional_notes,
				net_total: doc.grand_total,
				gst_amount: doc.gst_amount || 0,
				freight_amount: doc.freight_amount || 0,
				grand_total_with_tax: doc.grand_total_with_tax || doc.grand_total,
				attach_file: null,
				Encoterm:Encoterm
			};

			// 6️⃣ Read file if exists, then submit
			if (file) {
				let reader = new FileReader();
				reader.onload = function (e) {
					let base64Data = e.target.result.split(',')[1];
					other_details.attach_file = {
						file_name: file.name,
						content: base64Data
					};
					submitToFrappe(other_details);
				};
				reader.readAsDataURL(file);
			} else {
				submitToFrappe(other_details);
			}
		});
	}

	navigate_quotations() {
		$('.quotations').click(function(){
			name = $(this).attr('idx');
			window.location.href = "/quotations/" + encodeURIComponent(name);
		});
	}

	payment_terms_on_change() {
		var me = this;
		$('#payment_terms_template').on('change', function() {
			var selectedValue = $(this).val();
			var selectedText = $(this).find('option:selected').text();

			if (!selectedValue) {
				me.hidePaymentSchedule();
				return;
			}

			frappe.freeze();
			frappe.call({
				type: "POST",
				method: "vaaman.api.get_payment_schedule",
				args: { template_name: selectedText },
				btn: this,
				callback: function(r) {
					frappe.unfreeze();
					if (r.message) {
						me.createPaymentScheduleTable(r.message);
						me.showPaymentSchedule();
					} else {
						me.createPaymentScheduleTable([]);
						me.showPaymentSchedule();
					}
				},
				error: function(err) {
					frappe.unfreeze();
					me.hidePaymentSchedule();
				}
			});
		});
	}

	createPaymentScheduleTable(scheduleData) {
		const tbody = document.getElementById('paymentScheduleBody');
		if (!tbody) return;

		tbody.innerHTML = ''; // Clear existing content

		if (!scheduleData || scheduleData.length === 0) {
			tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No payment schedule available</td></tr>';
			return;
		}

		// Use grand total with tax for payment calculations
		const grandTotal = doc.grand_total_with_tax || doc.grand_total || 0;

		scheduleData.forEach((item, index) => {
			let percentage = parseFloat(item.invoice_portion) || 0;
			let amount = (grandTotal * percentage) / 100;

			const row = document.createElement('tr');
			row.innerHTML = `
				<td>${item.payment_term || 'N/A'}</td>
				<td>${item.description || 'N/A'}</td>
				<td>
					<input type="date"
						   class="form-control"
						   style="width: 150px;"
						   required>
				</td>
				<td class="text-right">${percentage}%</td>
				<td class="text-right">${format_number(amount, doc.number_format, 2)}</td>
			`;
			tbody.appendChild(row);
		});
	}

	showPaymentSchedule() {
		const container = document.getElementById('paymentScheduleContainer');
		if (container) {
			container.style.display = 'block';
		}
	}

	hidePaymentSchedule() {
		const container = document.getElementById('paymentScheduleContainer');
		if (container) {
			container.style.display = 'none';
		}
	}

	// UPDATED: Return grand total with tax
	get_final_amount(){
		return doc.grand_total_with_tax || doc.grand_total || 0;
	}
};