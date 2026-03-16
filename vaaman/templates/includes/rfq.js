// Copyright (c) 2015, Frappe Technologies Pvt. Ltd.
window.doc = {{ doc.as_json() }};

$(document).ready(function() {
	new rfq();
	doc.supplier = "{{ doc.supplier }}";
	doc.currency = "{{ doc.currency }}";
	doc.number_format = "{{ doc.number_format }}";
	doc.buying_price_list = "{{ doc.buying_price_list }}";
});

// Helper: GST percentage nikalne ke liye
function extract_gst_percent(gst_template) {
	if (!gst_template) return 0;
	let match = gst_template.match(/(\d+(\.\d+)?)\s*%/);
	return match ? flt(match[1]) : 0;
}

rfq = class rfq {

	constructor(){
		this.onfocus_select_all();
		this.change_qty();
		this.change_rate();
		this.change_discount();
		this.change_gst();
		this.update_freight_charges();
		this.terms();
		this.submit_rfq();
		this.navigate_quotations();

		this.calculate_all_totals();
	}

	onfocus_select_all(){
		$("input").click(function(){
			$(this).select();
		});
	}

	change_qty(){
		let me = this;
		$('.rfq-items').on("change", ".rfq-qty", function(){
			$(this).val(format_number(flt($(this).val()), doc.number_format, 2));
			me.calculate_all_totals();
		});
	}

	change_rate(){
		let me = this;
		$('.rfq-items').on("change", ".rfq-rate", function(){
			$(this).val(format_number(flt($(this).val()), doc.number_format, 2));
			me.calculate_all_totals();
		});
	}

	change_discount(){
		let me = this;
		$('.rfq-items').on("change", ".rfq-discount", function(){
			me.calculate_all_totals();
		});
	}

	change_gst(){
		let me = this;
		$('.rfq-items').on("change", ".rfq-gst", function(){
			me.calculate_all_totals();
		});
	}

	update_freight_charges(){
		let me = this;
		$(document).on("input change", "#freight_percentage", function(){
			me.calculate_all_totals();
		});
	}

	calculate_all_totals(){
		let total_pure_net = 0; 
		let total_gst_sum = 0;  

		doc.items.forEach(function(item){
			let idx = item.idx;

			let qty = flt($(`.rfq-qty[data-idx="${idx}"]`).val());
			let rate = flt($(`.rfq-rate[data-idx="${idx}"]`).val());
			let discount_p = flt($(`.rfq-discount[data-idx="${idx}"]`).val());

			let base_amount = qty * rate;
			let row_net_amount = base_amount * (1 - (discount_p / 100));

			let gst_template = $(`.rfq-gst[data-idx="${idx}"]`).val();
			let gst_p = extract_gst_percent(gst_template);
			let row_gst_amount = (row_net_amount * gst_p) / 100;

			item.qty = qty;
			item.rate = rate; 
			item.custom_discount_ = discount_p;
			item.item_tax_template = gst_template; 
			item.custom_gst_percent = gst_template; 
			item.amount = row_net_amount; 
			item.item_gst_amount = row_gst_amount;

			$(`.rfq-amount[data-idx="${idx}"]`)
				.text(format_number(row_net_amount, doc.number_format, 2));

			total_pure_net += row_net_amount;
			total_gst_sum += row_gst_amount;
		});

		let freight_p = flt($('#freight_percentage').val());
		let freight_amount = (total_pure_net * freight_p) / 100; 

		let grand_total = total_pure_net + total_gst_sum + freight_amount;

		doc.net_total = total_pure_net;
		doc.total_gst = total_gst_sum;
		doc.freight_percentage = freight_p;
		doc.freight_amount = freight_amount;
		doc.grand_total = grand_total;

		$('.tax-grand-total')
			.text(format_number(total_pure_net, doc.number_format, 2));
		
		$('#total_gst_amount')
			.text(format_number(total_gst_sum, doc.number_format, 2));
		
		$('#grand_total_with_tax')
			.val(format_number(grand_total, doc.number_format, 2));
	}

	submit_rfq(){
		let me = this;

		$(document).on('click', 'button[type="submit"]', function(e){
			e.preventDefault();
			
			let $btn = $(this);
			$btn.prop('disabled', true); // Prevent double submission

			me.calculate_all_totals();

			// 1. Prepare Item Details
			let item_details = doc.items.map(item => {
				let discounted_rate = flt(item.rate) * (1 - (flt(item.custom_discount_) / 100));
				return {
					item_code: item.item_code,
					qty: flt(item.qty),
					rate: discounted_rate, 
					custom_discount_: flt(item.custom_discount_),
					item_tax_template: item.item_tax_template, 
					custom_gst_percent: item.custom_gst_percent,
					amount: flt(item.amount),
					warehouse: item.warehouse
				};
			});

			// 2. Prepare Other Details
			let other_details = {
				freight_percentage: flt(doc.freight_percentage),
				freight_amount: flt(doc.freight_amount),
				net_total: flt(doc.net_total),
				total_gst: flt(doc.total_gst),
				grand_total: flt(doc.grand_total),
				payment_terms_template: $('#payment_terms_template').val(),
				incoterm: $('#encoterm_template').val(),
				notes: $('#document_notes').val()
			};

			// 3. Handle File Attachment logic
			let fileInput = document.getElementById('document_attachment');
			let file = fileInput.files[0];

			if (file) {
				let reader = new FileReader();
				reader.onload = function(e) {
					let file_data = {
						"filename": file.name,
						"content": e.target.result
					};
					// Send with attachment
					me.send_to_server(item_details, other_details, file_data, $btn);
				};
				reader.readAsDataURL(file);
			} else {
				// Send without attachment
				me.send_to_server(item_details, other_details, null, $btn);
			}
		});
	}

	// Helper function for API call
	send_to_server(item_details, other_details, attachment_data, $btn) {
		frappe.call({
			method: "vaaman.api.create_supplier_quotation",
			args: {
				doc: doc,
				item_details: JSON.stringify(item_details),
				other_details: JSON.stringify(other_details),
				attachment: attachment_data ? JSON.stringify(attachment_data) : null
			},
			callback: function(r){
				if (r.message) {
					window.location.href = "/supplier-quotations/" + r.message;
				} else {
					$btn.prop('disabled', false);
				}
			},
			error: function() {
				$btn.prop('disabled', false);
			}
		});
	}

	terms(){
		$(".terms-feedback").on("change", function(){
			doc.terms = $(this).val();
		});
	}

	navigate_quotations(){
		$('.quotations').click(function(){
			window.location.href = "/quotations/" + $(this).attr('idx');
		});
	}
};