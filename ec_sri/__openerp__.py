# -*- encoding: utf-8 -*-
########################################################################
#
# @authors: Christopher Ormaza
# Copyright (C) 2013  Ecuadorenlinea.net
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
# This module is GPLv3 or newer and incompatible
# with OpenERP SA "AGPL + Private Use License"!
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see http://www.gnu.org/licenses.
########################################################################

{
    "name" : "Documentos autorizados por el SRI",
    "version" : "2.0",
    'sequence': 4,
    'complexity': "easy",
    "author" : "SYSCOD Inc, syscod.comyr.com",
    "website" : "http://www.syscod.comyr.com/",
    "category" : "Regulación ecuatoriana",
    "depends" : [
                 'base',
                 'account',
                 'account_voucher',
                 'account_accountant',
                 'delivery',
                 'ec_ruc',
                 'purchase',
                 'sale',
                 'stock',
                 'report_aeroo',
                 'report_aeroo_ooo',
                 ],
    "description": """
    SRI es regualdor de las leyes de impuestos en Ecuador, 
    esta entidad emite las respectivas autorizaciones de facturas impresas, 
    retenciones, etc, para cada empresa.
    """,
    "init_xml": [],
    "update_xml": [ 
                    #'security/groups.xml',
                    #'security/ir.model.access.csv',
                    'data/ecuadorian_data.xml',
                    'data/shop_data.xml',
                    'data/sequence_data.xml',
                    'data/ice_codes.xml',
                    'data/ice_tax.xml',
                    #'report/withhold_report.xml',
                                                    #'workflow/invoice_workflow.xml',
                    #'workflow/retention_workflow.xml',
                    #'wizard/retention_wizard_view.xml',
                    #'wizard/wizard_credit_note_view.xml',
                    'wizard/invoice_print_wizard.xml',
                    'wizard/authorization_wizard.xml',
                    'views/authorization_view.xml',
                    'views/company_view.xml',
                    'views/document_type_view.xml',
                    'views/partner_view.xml',
                    'views/product_view.xml',
                    #'views/sale_order_view.xml',
                    'views/shop_view.xml',
                    'views/user_view.xml',
                    #'views/withhold_view.xml',
                    'views/invoice_view.xml',
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}
