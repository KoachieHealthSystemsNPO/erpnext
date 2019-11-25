# -*- coding: utf-8 -*-
# Copyright (c) 2018-2019, lasalesi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import datetime

class SalesReport(Document):
    def onload(self):
        return

    def setup(self):
        return

    def refresh(self):
        return

    """ This function is called in a script fashion to populate the report 
        It can be executed from the wrapper
            erpnext.selling.doctype.sales_report.sales_report.create_report
    """
    def fill(self, sales_person):
        # prepare global variables
        today = datetime.now()
        self.date = today.strftime("%Y-%m-%d")
        self.week = today.strftime("%W")
        self.title = "Sales Report " + str(self.date)
        self.sales_person = sales_person
        if sales_person != "%":
            self.title += " " + sales_person
        _week = int(today.strftime("%W"))
        _this_year = int(today.strftime("%Y"))
        _last_year = _this_year - 1
        self.this_year = _this_year
        self.last_year = _last_year

        group_sql = """SELECT `title` FROM `tabSales Report Group`
                    ORDER BY `prio` DESC;"""
        groups = frappe.db.sql(group_sql, as_dict=True)
        for group in groups:
            _description = group['title']
            _sql_7days = """SELECT (IFNULL(SUM(`kg`), 0)) AS `qty`,
                    (IFNULL(SUM(`net_amount`), 0)) AS `revenue`
                FROM `viewDelivery`
                WHERE `sales_report_group` = '{filter}'
                AND `docstatus` = 1
                AND `posting_date` > DATE_SUB(NOW(), INTERVAL 7 DAY)
                AND `sales_person` LIKE '{sales_person}'
                """.format(filter=group['title'], sales_person=sales_person)
            _qty_7days,_revenue_7days = get_qty_revenue(_sql_7days)
            _sql_YTD = """SELECT (IFNULL(SUM(`kg`), 0)) AS `qty`,
                    (IFNULL(SUM(`net_amount`), 0)) AS `revenue`
                FROM `viewDelivery`
                WHERE `sales_report_group` = '{filter}'
                AND `docstatus` = 1
                AND `posting_date` >= '{year}-01-01'
                AND `sales_person` LIKE '{sales_person}'
                """.format(year=today.strftime("%Y"), filter=group['title'], sales_person=sales_person)
            _qty_YTD,_revenue_YTD = get_qty_revenue(_sql_YTD)
            _sql_PY = """SELECT (IFNULL(SUM(`kg`), 0)) AS `qty`,
                    (IFNULL(SUM(`net_amount`), 0)) AS `revenue`
                FROM `viewDelivery`
                WHERE `sales_report_group` = '{filter}'
                AND `docstatus` = 1
                AND `posting_date` >= '{year}-01-01'
                AND `posting_date` <= '{year}-12-31'
                AND `sales_person` LIKE '{sales_person}'
                """.format(year=int(today.strftime("%Y")) - 1, filter=group['title'], sales_person=sales_person)
            _qty_PY,_revenue_PY = get_qty_revenue(_sql_PY)

            self.append('items',
                {
                    'description': _description,
                    'qty_7days': _qty_7days,
                    'revenue_7days': _revenue_7days,
                    'qty_ytd': _qty_YTD,
                    'revenue_ytd': _revenue_YTD,
                    'qty_py': _qty_PY,
                    'revenue_py': _revenue_PY,
                    'demand_qty_ytd': (_qty_YTD/_week),
                    'demand_revenue_ytd': (_revenue_YTD/_week),
                    'demand_qty_py': (_qty_PY/52),
                    'demand_revenue_py': (_revenue_PY/52)
                })

        # compute totals
        self.update_totals()
        return

    def update_totals(self):
        _total_qty_7days = 0
        _total_qty_ytd = 0 
        _total_demand_qty_ytd = 0
        _total_demand_qty_py = 0
        _total_qty_py = 0
        _total_revenue_7days = 0
        _total_revenue_ytd = 0
        _total_demand_revenue_ytd = 0
        _total_demand_revenue_py = 0
        _total_revenue_py = 0
        try:
            if self.items:
                for item in self.items:
                    _total_qty_7days = _total_qty_7days + item.qty_7days
                    _total_qty_ytd = _total_qty_ytd + item.qty_ytd
                    _total_demand_qty_ytd = _total_demand_qty_ytd + item.demand_qty_ytd
                    _total_demand_qty_py = _total_demand_qty_py + item.demand_qty_py
                    _total_qty_py = _total_qty_py + item.qty_py
                    _total_revenue_7days = _total_revenue_7days + item.revenue_7days
                    _total_revenue_ytd = _total_revenue_ytd + item.revenue_ytd
                    _total_demand_revenue_ytd = _total_demand_revenue_ytd + item.demand_revenue_ytd
                    _total_demand_revenue_py = _total_demand_revenue_py + item.demand_revenue_py
                    _total_revenue_py = _total_revenue_py + item.revenue_py
        except:
            pass
        self.total_qty_7days = _total_qty_7days
        self.total_qty_ytd = _total_qty_ytd
        self.total_demand_qty_ytd = _total_demand_qty_ytd
        self.total_demand_qty_py = _total_demand_qty_py
        self.total_qty_py = _total_qty_py
        self.total_revenue_7days = _total_revenue_7days
        self.total_revenue_ytd = _total_revenue_ytd
        self.total_demand_revenue_ytd = _total_demand_revenue_ytd
        self.total_demand_revenue_py = _total_demand_revenue_py
        self.total_revenue_py = _total_revenue_py
        return

@frappe.whitelist()
def create_report(sales_person="%"):
    new_report = frappe.get_doc({"doctype": "Sales Report"})
    new_report.fill(sales_person)
    new_report_name = new_report.insert()
    return

""" Extracts `result` from SQL query """
def get_value(sql):
    values = frappe.db.sql(sql, as_dict=True)
    return values[0].result

""" Extracts `qty` and `revenue` from SQL query """
def get_qty_revenue(sql):
    values = frappe.db.sql(sql, as_dict=True)
    return values[0].qty, values[0].revenue
