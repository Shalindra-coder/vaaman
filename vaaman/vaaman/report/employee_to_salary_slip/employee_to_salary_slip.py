# Copyright (c) 2025, Pratul Tiwari and contributors
# For license information, please see license.txt


import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"fieldname": "employee", "label": "Employee No", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"fieldname": "employee_name", "label": "Full Name", "fieldtype": "Data", "width": 160},
        {"fieldname": "date_of_joining", "label": "Joining Date", "fieldtype": "Date", "width": 100},
        {"fieldname": "gender", "label": "Gender", "fieldtype": "Data", "width": 80},
     
        {"fieldname": "department", "label": "Department", "fieldtype": "Link", "options": "Department", "width": 140},
        {"fieldname": "designation", "label": "Designation", "fieldtype": "Link", "options": "Designation", "width": 140},
        {"fieldname": "branch", "label": "Branch", "fieldtype": "Link", "options": "Branch", "width": 140},
        {"fieldname": "company", "label": "Company", "fieldtype": "Link", "options": "Company", "width": 140},
     
        {"fieldname": "payment_days", "label": "Present Days", "fieldtype": "Float", "width": 100},
        {"fieldname": "leave_without_pay", "label": "Leave (LWP)", "fieldtype": "Float", "width": 90},
        {"fieldname": "total_working_days", "label": "Fixed Monthly Days", "fieldtype": "Float", "width": 120},
        {"fieldname": "gross_pay", "label": "Gross Pay", "fieldtype": "Currency", "width": 120},
        {"fieldname": "net_pay", "label": "Net Pay", "fieldtype": "Currency", "width": 120},
        {"fieldname": "rounded_total", "label": "Paid Amount", "fieldtype": "Currency", "width": 120},
        {"fieldname": "difference", "label": "Difference", "fieldtype": "Currency", "width": 100},
        
        {"fieldname": "full_basic", "label": "Full Basic", "fieldtype": "Currency", "width": 110},
        {"fieldname": "full_hra", "label": "Full HRA", "fieldtype": "Currency", "width": 110},
        {"fieldname": "full_conveyance_allowance", "label": "Full Conveyance", "fieldtype": "Currency", "width": 120},
        {"fieldname": "full_mobile_allowance", "label": "Full Mobile Allowance", "fieldtype": "Currency", "width": 130},
        {"fieldname": "full_medical_allowance", "label": "Full Medical Allowance", "fieldtype": "Currency", "width": 130},
        {"fieldname": "full_children_education_allowance", "label": "Full Children Education", "fieldtype": "Currency", "width": 140},
        {"fieldname": "full_uniform_washing_allowance", "label": "Full Uniform Washing", "fieldtype": "Currency", "width": 140},
        {"fieldname": "full_lta", "label": "Full LTA", "fieldtype": "Currency", "width": 110},
        {"fieldname": "full_location_allowance", "label": "Full Location Allowance", "fieldtype": "Currency", "width": 140},
        {"fieldname": "full_others_allowance", "label": "Full Others Allowance", "fieldtype": "Currency", "width": 130},
        {"fieldname": "basic", "label": "Basic", "fieldtype": "Currency", "width": 110},
        {"fieldname": "hra", "label": "HRA", "fieldtype": "Currency", "width": 110},
        {"fieldname": "conveyance_allowance", "label": "Conveyance", "fieldtype": "Currency", "width": 120},
        {"fieldname": "mobile_allowance", "label": "Mobile Allowance", "fieldtype": "Currency", "width": 130},
        {"fieldname": "medical_allowance", "label": "Medical Allowance", "fieldtype": "Currency", "width": 130},
        {"fieldname": "children_education_allowance", "label": "Children Education", "fieldtype": "Currency", "width": 140},
        {"fieldname": "uniform_washing_allowance", "label": "Uniform Washing", "fieldtype": "Currency", "width": 140},
        {"fieldname": "lta", "label": "LTA", "fieldtype": "Currency", "width": 110},
        {"fieldname": "location_allowance", "label": "Location Allowance", "fieldtype": "Currency", "width": 140},
        {"fieldname": "others_allowance", "label": "Others Allowance", "fieldtype": "Currency", "width": 130},
        {"fieldname": "provident_fund", "label": "PF", "fieldtype": "Currency", "width": 100},
        {"fieldname": "professional_tax", "label": "Prof Tax", "fieldtype": "Currency", "width": 100},
        {"fieldname": "income_tax", "label": "Income Tax", "fieldtype": "Currency", "width": 100},
        {"fieldname": "salary_advance", "label": "Salary Advance", "fieldtype": "Currency", "width": 110},
        {"fieldname": "loan_repayment", "label": "Loan", "fieldtype": "Currency", "width": 100},
        {"fieldname": "bank_name", "label": "Bank Name", "fieldtype": "Data", "width": 150},
        {"fieldname": "bank_ac_no", "label": "Bank Account", "fieldtype": "Data", "width": 150},
        {"fieldname": "ifsc_code", "label": "IFSC Code", "fieldtype": "Data", "width": 120},
    ]

def get_data(filters):
    conditions = ""
  
    if filters.get("from_date"):
        conditions += " AND ss.start_date >= %(from_date)s"
    if filters.get("to_date"):
        conditions += " AND ss.end_date <= %(to_date)s"
    if filters.get("employee"):
        conditions += " AND ss.employee = %(employee)s"
    if filters.get("company"):
        conditions += " AND ss.company = %(company)s"

    if filters.get("department"):
        conditions += " AND emp.department = %(department)s"
    if filters.get("designation"):
        conditions += " AND emp.designation = %(designation)s"
    if filters.get("branch"):
        conditions += " AND emp.branch = %(branch)s"

    sql_query = f"""
        SELECT
            ss.employee, ss.employee_name, emp.date_of_joining, emp.gender,ss.company,
            emp.department, emp.designation, emp.branch,
            ss.payment_days, ss.leave_without_pay, ss.total_working_days,
            ss.gross_pay, ss.net_pay, ss.rounded_total, (ss.rounded_total - ss.net_pay) AS difference,
            emp.bank_name, emp.bank_ac_no, emp.ifsc_code,

            (SELECT amount FROM `tabSalary Detail` sd_struct WHERE sd_struct.parent=ss.salary_structure AND sd_struct.salary_component='Basic' AND sd_struct.parenttype='Salary Structure') AS full_basic,
            (SELECT amount FROM `tabSalary Detail` sd_struct WHERE sd_struct.parent=ss.salary_structure AND sd_struct.salary_component='HRA' AND sd_struct.parenttype='Salary Structure') AS full_hra,
            (SELECT amount FROM `tabSalary Detail` sd_struct WHERE sd_struct.parent=ss.salary_structure AND sd_struct.salary_component='Conveyance Allowance' AND sd_struct.parenttype='Salary Structure') AS full_conveyance_allowance,
            (SELECT amount FROM `tabSalary Detail` sd_struct WHERE sd_struct.parent=ss.salary_structure AND sd_struct.salary_component='Mobile Allowance' AND sd_struct.parenttype='Salary Structure') AS full_mobile_allowance,
            (SELECT amount FROM `tabSalary Detail` sd_struct WHERE sd_struct.parent=ss.salary_structure AND sd_struct.salary_component='Medical Allowance' AND sd_struct.parenttype='Salary Structure') AS full_medical_allowance,
            (SELECT amount FROM `tabSalary Detail` sd_struct WHERE sd_struct.parent=ss.salary_structure AND sd_struct.salary_component='Children Education Allowance' AND sd_struct.parenttype='Salary Structure') AS full_children_education_allowance,
            (SELECT amount FROM `tabSalary Detail` sd_struct WHERE sd_struct.parent=ss.salary_structure AND sd_struct.salary_component='Uniform Washing Allowance' AND sd_struct.parenttype='Salary Structure') AS full_uniform_washing_allowance,
            (SELECT amount FROM `tabSalary Detail` sd_struct WHERE sd_struct.parent=ss.salary_structure AND sd_struct.salary_component='LTA' AND sd_struct.parenttype='Salary Structure') AS full_lta,
            (SELECT amount FROM `tabSalary Detail` sd_struct WHERE sd_struct.parent=ss.salary_structure AND sd_struct.salary_component='Location Allowance' AND sd_struct.parenttype='Salary Structure') AS full_location_allowance,
            (SELECT amount FROM `tabSalary Detail` sd_struct WHERE sd_struct.parent=ss.salary_structure AND sd_struct.salary_component='Others Allowance' AND sd_struct.parenttype='Salary Structure') AS full_others_allowance,
            
            (SELECT amount FROM `tabSalary Detail` sd WHERE sd.parent=ss.name AND sd.salary_component='Basic') AS basic,
            (SELECT amount FROM `tabSalary Detail` sd WHERE sd.parent=ss.name AND sd.salary_component='HRA') AS hra,
            (SELECT amount FROM `tabSalary Detail` sd WHERE sd.parent=ss.name AND sd.salary_component='Conveyance Allowance') AS conveyance_allowance,
            (SELECT amount FROM `tabSalary Detail` sd WHERE sd.parent=ss.name AND sd.salary_component='Mobile Allowance') AS mobile_allowance,
            (SELECT amount FROM `tabSalary Detail` sd WHERE sd.parent=ss.name AND sd.salary_component='Medical Allowance') AS medical_allowance,
            (SELECT amount FROM `tabSalary Detail` sd WHERE sd.parent=ss.name AND sd.salary_component='Children Education Allowance') AS children_education_allowance,
            (SELECT amount FROM `tabSalary Detail` sd WHERE sd.parent=ss.name AND sd.salary_component='Uniform Washing Allowance') AS uniform_washing_allowance,
            (SELECT amount FROM `tabSalary Detail` sd WHERE sd.parent=ss.name AND sd.salary_component='LTA') AS lta,
            (SELECT amount FROM `tabSalary Detail` sd WHERE sd.parent=ss.name AND sd.salary_component='Location Allowance') AS location_allowance,
            (SELECT amount FROM `tabSalary Detail` sd WHERE sd.parent=ss.name AND sd.salary_component='Others Allowance') AS others_allowance,
            
            (SELECT amount FROM `tabSalary Detail` sd WHERE sd.parent=ss.name AND sd.salary_component='Provident Fund') AS provident_fund,
            (SELECT amount FROM `tabSalary Detail` sd WHERE sd.parent=ss.name AND sd.salary_component='Professional Tax') AS professional_tax,
            (SELECT amount FROM `tabSalary Detail` sd WHERE sd.parent=ss.name AND sd.salary_component='Income Tax') AS income_tax,
            (SELECT amount FROM `tabSalary Detail` sd WHERE sd.parent=ss.name AND sd.salary_component='Salary Advance') AS salary_advance,
            (SELECT SUM(amount) FROM `tabSalary Detail` sd WHERE sd.parent=ss.name AND sd.salary_component LIKE '%%Loan%%') AS loan_repayment

        FROM `tabSalary Slip` AS ss
        JOIN `tabEmployee` AS emp ON ss.employee = emp.name
        WHERE ss.docstatus IN (0, 1, 2) {conditions}
        ORDER BY ss.employee_name, ss.start_date
    """

    data = frappe.db.sql(sql_query, filters, as_dict=True)
    return data

