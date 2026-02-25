// Copyright (c) 2026, Pratul Tiwari and contributors
// For license information, please see license.txt

frappe.query_reports["Supplier Quotation Comparative"] = {
  filters: [
    {
      fieldname: "rfq",
      label: __("Request for Quotation"),
      fieldtype: "Link",
      options: "Request for Quotation",
      reqd: 1,

    },
    {
      fieldname: "company",
      label: __("Company"),
      fieldtype: "Link",
      options: "Company",

    },
    {
      fieldname: "from_date",
      label: __("From Date"),
      fieldtype: "Date",
      default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),

    },
    {
      fieldname: "to_date",
      label: __("To Date"),
      fieldtype: "Date",
      default: frappe.datetime.get_today(),

    },
    {
      fieldname: "item_code",
      label: __("Item"),
      fieldtype: "Link",
      options: "Item",

    },
    {
      fieldname: "supplier",
      label: __("Supplier"),
      fieldtype: "Link",
      options: "Supplier",

    },
    {
      fieldname: "supplier_quotation",
      label: __("Supplier Quotation"),
      fieldtype: "Link",
      options: "Supplier Quotation",

    },
    {
      fieldname: "group_by",
      label: __("Categorize By"),
      fieldtype: "Select",
      options: ["Categorize by Supplier", "Categorize by Item"],
      default: "Categorize by Supplier",

    }
  ],

  onload: function (report) {

    frappe.require("/assets/vaaman/css/supplier_quotation_comparative.css");

  },


  refresh: function (report) {
    if (report.data && report.data.length > 0) {
      render_custom_report();
    }
  },

  after_datatable_render: function (datatable) {
    if (frappe.query_report.data && frappe.query_report.data.length > 0) {

      render_custom_report();
    }
  }
};


function render_custom_report() {
  let data = frappe.query_report.data;
  let columns = frappe.query_report.columns;
  let wrapper = frappe.query_report.$report[0];

  if (!wrapper || !data || data.length === 0) return;


  $(wrapper).find(".no-result").hide();
  $(wrapper).find(".datatable").hide();


  if ($(wrapper).find("#custom-report").length === 0) {
    $(wrapper).append(`
            <div id="custom-report">
                <div class="table-wrapper">
                    <table class="custom-table">
                        <thead id="custom-thead"></thead>
                        <tbody id="custom-tbody"></tbody>
                    </table>
                </div>
            </div>
        `);
  }

  build_table(columns, data);
}

// --- TABLE BUILDING LOGIC ---
function build_table(columns, data) {
  let thead = document.getElementById("custom-thead");
  let tbody = document.getElementById("custom-tbody");
  if (!thead || !tbody) return;

  // Supplier grouping logic
  let supplier_map = {};
  columns.forEach(col => {
    if (col.supplier_name) {
      if (!supplier_map[col.supplier_name]) supplier_map[col.supplier_name] = [];
      supplier_map[col.supplier_name].push(col);
    }
  });

  // Header Row 1
  let h1 = `<tr>
        <th rowspan="2">S. No</th>
        <th rowspan="2">Item Description</th>
        <th rowspan="2">QTY</th>
        <th rowspan="2">UOM</th>
        <th rowspan="2">HSN</th>
        <th rowspan="2">GST %</th>
        <th rowspan="2">LPP Rate</th>`;

  Object.keys(supplier_map).forEach(supplier => {
    h1 += `<th colspan="3" class="co-group-header">${supplier}</th>`;
  });

  h1 += `<th colspan="3" class="co-group-header">L1 For Each Item</th></tr>`;

  // -------- HEADER ROW 2 --------
  let h2 = "<tr>";
  Object.values(supplier_map).forEach(() => {
    h2 += `<th>Initial</th><th>Negotiated</th><th>Total</th>`;
  });
  h2 += `<th>Initial</th><th>Negotiated</th><th>Supplier</th></tr>`;

  thead.innerHTML = h1 + h2;

  // -------- BODY --------
  tbody.innerHTML = "";

  data.forEach(row => {
    let tr = "";

    // ================= SUMMARY ROW =================
    if (row.is_summary) {

      tr += `
        <tr style="
            font-weight:500;
              border-top:2px solid #ebe2e2;
          ${(
          row.item_description === "Basic Total" ||
          row.item_description === "Supplier Ranking on total with GST" ||
          row.item_description === "Grand Total With GST"
        ) ? "background:#1b1e3f; color:white;" : ""}
">
      `;


      tr += `
        <td colspan="7" style="text-align:left;padding:4px;">
          ${row.item_description}
        </td>
      `;


      Object.values(supplier_map).forEach(cols => {

        // find total column of current supplier
        let total_col = cols.find(c => c.fieldname.endsWith("_total"));

        let val = "";

        if (total_col) {

          // Payment Terms row
          if (row.item_description === "Payment Terms") {
            let payment_field = total_col.fieldname.replace("_total", "_payment_terms");
            val = row[payment_field] || "";
          }

          // Incoterms row
          else if (row.item_description === "IncoTerms") {
            let inco_field = total_col.fieldname.replace("_total", "_incoterms");
            val = row[inco_field] || "";
          }

          // Normal summary rows
          else {
            val = row[total_col.fieldname] || "";
            if (val && !isNaN(val)) {
              val = flt(val, 2); // Yahan decimal fix hoga
            }
          }
        }

        if (val) {
          if (row.item_description === "Supplier Ranking on total with GST") {
            val = "L" + val;
            if (val === "L1") {
              val = `<span style="font-weight:bold;text-align:center">${val}</span>`;
            }
          }

          else if (
            row.item_description === "Basic Total" ||
            row.item_description === "Grand Total With GST"
          ) {
            val = frappe.format(flt(val, 2), { fieldtype: "Float" });
          }
        }

        tr += `
    <td colspan="3" style="text-align:right;">
      ${val}
    </td>
  `;
      });

      // L1 blank
      tr += `<td></td><td></td><td></td>`;
    }

    // ================= NORMAL ITEM ROW =================
    else {
      tr += "<tr>";

      tr += `
        <td>${row.s_no ?? ""}</td>
        <td>${row.item_description ?? ""}</td>
        <td>${row.qty ?? ""}</td>
        <td>${row.uom ?? ""}</td>
        <td>${row.hsn ?? ""}</td>
        <td>${row.gst ?? ""}%</td>
        <td>${row.lpp_rate ?? ""}</td>
      `;

      // supplier values
      Object.values(supplier_map).forEach(cols => {
        cols.forEach(col => {
          tr += `<td>${row[col.fieldname] ?? ""}</td>`;
        });
      });

      // L1 values
      tr += `
        <td>${row.l1_initial ?? ""}</td>
        <td>${row.l1_negotiated ?? ""}</td>
        <td class="supplier-col">${row.l1_supplier ?? ""}</td>
      `;
    }

    tr += "</tr>";
    tbody.innerHTML += tr;
  });
}

