// Copyright (c) 2015, Frappe Technologies Pvt. Ltd.

window.doc = {{ doc.as_json() }};

$(document).ready(function() {
	new rfq();
	doc.supplier = "{{ doc.supplier }}";
	doc.currency = "{{ doc.currency }}";
	doc.number_format = "{{ doc.number_format }}";
	doc.buying_price_list = "{{ doc.buying_price_list }}";
});


/* =====================================
	GST % EXTRACT FROM TEMPLATE NAME
	Example: "GST 18% - PP" => 18
===================================== */
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

		// Initial calculation
		this.calculate_all_totals();
	}

	onfocus_select_all(){
		$("input").click(function(){
			$(this).select();
		});
	}

	/* ============= EVENTS ============= */

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
		$(document).on("change", "#freight_percentage", function(){
			me.calculate_all_totals();
		});
	}

	/* ============= CORE CALCULATION ============= */

	calculate_all_totals(){
		let total_net_amount = 0;
		let total_gst_amount = 0;

		doc.items.forEach(function(item){
			let idx = item.idx;

			let qty = flt($(`.rfq-qty[data-idx="${idx}"]`).val());
			let rate = flt($(`.rfq-rate[data-idx="${idx}"]`).val());
			let discount_p = flt($(`.rfq-discount[data-idx="${idx}"]`).val());

			// STEP 1: Base amount
			let base_amount = qty * rate;

			// STEP 2: Discount
			let row_net_amount = base_amount - (base_amount * (discount_p / 100));

			// STEP 3: GST from Item Tax Template (UI dropdown value)
			let gst_template = $(`.rfq-gst[data-idx="${idx}"]`).val();
			let gst_p = extract_gst_percent(gst_template);

			// STEP 4: GST amount
			let row_gst_amount = (row_net_amount * gst_p) / 100;

			// STEP 5: Row total
			let row_total = row_net_amount + row_gst_amount;

			// Save to doc object
			item.qty = qty;
			item.rate = rate;
			item.custom_discount_ = discount_p;
			item.item_tax_template = gst_template; 
			item.custom_gst_percent = gst_template; // 🔥 Custom Link field ke liye value assign ki
			item.amount = row_net_amount;
			item.item_gst_amount = row_gst_amount;

			// UI update
			$(`.rfq-amount[data-idx="${idx}"]`)
				.text(format_number(row_total, doc.number_format, 2));

			total_net_amount += row_net_amount;
			total_gst_amount += row_gst_amount;
		});

		// STEP 6: Freight on (Net + GST)
		let net_plus_gst = total_net_amount + total_gst_amount;
		let freight_p = flt($('#freight_percentage').val());
		let freight_amount = (net_plus_gst * freight_p) / 100;

		// STEP 7: Grand Total
		let grand_total = net_plus_gst + freight_amount;

		// Save header values
		doc.net_total = total_net_amount;
		doc.total_gst = total_gst_amount;
		doc.freight_percentage = freight_p;
		doc.freight_amount = freight_amount;
		doc.grand_total = grand_total;

		// UI SUMMARY
		$('.tax-net-total').text(format_number(total_net_amount, doc.number_format, 2));
		$('#display_total_gst').text(format_number(total_gst_amount, doc.number_format, 2));
		$('#display_freight_amount').text(format_number(freight_amount, doc.number_format, 2));
		$('.tax-grand-total').text(format_number(grand_total, doc.number_format, 2));
		$('#grand_total_with_tax').val(format_number(grand_total, doc.number_format, 2));
	}

	/* ============= SUBMIT ============= */

	submit_rfq(){
		let me = this;

		$('.btn-lg').click(function(){
			me.calculate_all_totals();

			let item_details = doc.items.map(item => ({
				item_code: item.item_code,
				qty: flt(item.qty),
				rate: flt(item.rate),
				custom_discount_: flt(item.custom_discount_),
				item_tax_template: item.item_tax_template, 
				custom_gst_percent: item.custom_gst_percent, // 🔥 Supplier Quotation Item table mein jayega
				amount: flt(item.amount),
				warehouse: item.warehouse
			}));

			let other_details = {
				freight_percentage: flt(doc.freight_percentage),
				freight_amount: flt(doc.freight_amount),
				net_total: flt(doc.net_total),
				total_gst: flt(doc.total_gst),
				grand_total: flt(doc.grand_total),
				payment_terms_template: $('#payment_terms_template').val(),
				incoterm: $('#encoterm_template').val()
			};

			frappe.call({
				method: "vaaman.api.create_supplier_quotation",
				args: {
					doc: doc,
					item_details: JSON.stringify(item_details),
					other_details: JSON.stringify(other_details)
				},
				callback: function(r){
					if (r.message) {
						window.location.href = "/supplier-quotations/" + r.message;
					}
				}
			});
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