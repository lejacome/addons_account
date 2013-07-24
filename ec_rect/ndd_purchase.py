# -*- coding: utf-8 -*-
#############################################################################
#     OpenERP, Open Source Management Solution                              #
#     Copyright (C) 2013  ed.winTG, www.syscod.com                          #
#                                                                           #
#    This program is free software: you can redistribute it and/or modify   #
#    it under the terms of the GNU General Public License as published by   #
#    the Free Software Foundation, either version 3 of the License, or      #
#    (at your option) any later version.                                    #
#                                                                           #
#    This program is distributed in the hope that it will be useful,        #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#    GNU General Public License for more details.                           #
#                                                                           #
#    You should have received a copy of the GNU General Public License      #
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#############################################################################



import logging
from osv import fields, osv
import netsvc, tools
import time
from tools.translate import _

_logger = logging.getLogger(__name__)



class ecua_ndd_purchase(osv.osv):
    _name = 'ecua.ndd.purchase'
    _inherits={'documentos.complementarios':'document_id'}
    _description='Debit Notes'

    def check_ref(self, cr, uid, ids):
        partner_obj = self.pool.get('res.partner')
        for data in self.browse(cr, uid, ids):
            return partner_obj.check_ced(data.ruc).get('valid', False)
    
    def _default_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id and user.company_id.id or False

    _columns = {
                 'document_id': fields.many2one('documentos.complementarios','Document',ondelete='cascade'),
                 'ndd_line_ids':fields.one2many('ecua.ndd_line','ecua_ndd_id','Lineas N. Debito'),               
                 'ndd_concept':fields.selection([
                ('error','Error de Facturacion'),
                ('interes','Intereses'),
                ('flete','Gastos por fletes'),
                ('banco','Gastos bancarios')],'Concepto', select=True),
             }

    _defaults = {'company_id':_default_company,
                 'denominacion': 'Debit Note',
                 'is_ndd': lambda *a: 1, 
                 'state': 'draft',
               }
    
    def onChange_comprobante(self, cr, uid, ids, comprobante_id, context=None):
        values={}
        comprobant=self.pool.get('account.invoice').browse(cr, uid,comprobante_id, context)
        values['customer_name']=comprobant.partner_id.name
        values['customer_ruc']=comprobant.partner_id.ref
        if comprobant.period_id:
            values['ejercicio_fiscal']=comprobant.period_id.fiscalyear_id.name
        #phone para el telefono
        address="";
        if(comprobant.partner_id.street):
            address=comprobant.partner_id.street
        if (comprobant.partner_id.street2):
            address=address+" & "+comprobant.partner_id.street2 
        if(comprobant.partner_id.city):
            address=address+" - "+comprobant.partner_id.city         
        values['customer_dir']=address
        return {'value': values}
    
    def onchange_data(self, cr, uid, ids, doc_number, shop_id=None, date=None, context=None):
        if context is None: context = {}
        shops_domain_ids = []
        domain = {}
        values={}        
        warning = {}
        if not doc_number and not shop_id:
            return {}
        if not doc_number:
            warning = {
                       'title': _('Warning!!!'),
                       'message': _('Document must have a printer point selected to validate number!!!'),
                       }
            return {'warning': warning}
        printer_obj = self.pool.get('sri.printer.point')
        doc_obj=self.pool.get('sri.type.document')
        auth_obj = self.pool.get('sri.authorization')
        shop_obj = self.pool.get('sale.shop')
        curr_user = self.pool.get('res.users').browse(cr, uid, uid, context)
        curr_shop = shop_id and shop_obj.browse(cr, uid, shop_id, context) or None
        journal_id = curr_shop.sales_journal_id and curr_shop.sales_journal_id.id or None
        name_document = 'credit_note'
        name_field = 'doc_number'
        values['journal_id'] = journal_id
        printer = None
        if curr_user.printer_default_id:
            printer = curr_user.printer_default_id
        if not printer:
            for shop in curr_user.shop_ids:
                for printer_id in shop.printer_point_ids:
                    printer = printer_id
                    break
        if printer:
            values['shop_id'] = printer.shop_id.id
            values['printer_id'] = printer.id
            printer_id=printer.id
            
        #import pdb
        #pdb.set_trace()    
        
        if curr_shop:
            if doc_number and printer_id:
                shops_domain_ids.append(curr_shop.id)
                auth = self.pool.get('sri.authorization').check_if_seq_exist(cr, uid, name_document, doc_number, printer_id , date, context)
                authorization = auth and auth_obj.browse(cr, uid, auth['authorization'], context) or None
                values['num_atoriza'] = authorization.number 
                values['shop_id'] = curr_shop.id
                values['autoriza_date_emision'] = authorization.start_date
                values['autoriza_date_expire'] = authorization.expiration_date              
        else:
            curr_user.printer_default_id and curr_user.printer_default_id.shop_id and shops_domain_ids.append(curr_user.printer_default_id.shop_id.id)
            for shop_allowed in curr_user.shop_ids:
                shops_domain_ids.append(shop_allowed.id)
            auth_line_id = doc_obj.search(cr, uid, [('name','=',name_document), ('printer_id','=',printer_id), ('state','=',True)])
            if auth_line_id:
                auth_line = doc_obj.browse(cr, uid, auth_line_id[0],context)
                values['num_atoriza'] = auth_line.sri_authorization_id.number
                values['autoriza_date_emision'] = auth_line.sri_authorization_id.start_date
                values['autoriza_date_expire'] = auth_line.sri_authorization_id.expiration_date
                next_number = doc_obj.get_next_value_secuence(cr, uid, name_document, False, printer_id, 'ecua.ndd', name_field, context)
                values[name_field] = next_number#'001-001-000000005'
                values['fecha_emision'] = time.strftime('%Y-%m-%d')
            else:
                if printer_id and curr_shop:
                    printer = printer_obj.browse(cr, uid, printer_id, context)
                    warning = {
                               'title': _("There's not any authorization for generate documents for data input: Agency %s Printer Point %s") % (curr_shop.number, printer.name)
                               }
        domain['shop_id'] = [('id','in', shops_domain_ids)]
        return {'value': values, 'domain':domain, 'warning': warning}
        
    def default_get(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        doc_obj=self.pool.get('sri.type.document')
        values={}
        if not values:
            values={}
        curr_user = self.pool.get('res.users').browse(cr, uid, uid, context)
        values['ruc'] = curr_user.company_id.ruc
        #ADDRESS COMPANY
        address="";
        if(curr_user.company_id.street):
            address=curr_user.company_id.street
        if (curr_user.company_id.street2):
            address=address+" & "+curr_user.company_id.street2 
        if(curr_user.company_id.city):
            address=address+" - "+curr_user.company_id.city  
        values["dir_matriz"]=address
        values["company_id"]=curr_user.company_id.id
        #Hay que primero agregar un campo direccion en sales.shop...o tienda para poder sacar este campo
        values["dir_sucursal"]=address 
        values["nom_comercial"]=curr_user.company_id.name
        #Hay que primero agregar este campo en res.company, para poder sacar este campo
        values["razon_social"]=curr_user.company_id.name 
        printer = None
        if curr_user.printer_default_id:
            printer = curr_user.printer_default_id
        if not printer:
            for shop in curr_user.shop_ids:
                for printer_id in shop.printer_point_ids:
                    printer = printer_id
                    break
        if printer:
            values['shop_id'] = printer.shop_id.id
            values['printer_id'] = printer.id
            if ('doc_number') in fields_list:
                auth_line_id = doc_obj.search(cr, uid, [('name','=','debit_note'), ('printer_id','=',printer.id), ('state','=',True)])
                if auth_line_id:
                    auth_line = doc_obj.browse(cr, uid, auth_line_id[0],context)
                    values['num_atoriza'] = auth_line.sri_authorization_id.number
                    values['autoriza_date_emision'] = auth_line.sri_authorization_id.start_date
                    values['autoriza_date_expire'] = auth_line.sri_authorization_id.expiration_date
                    values['doc_number'] = doc_obj.get_next_value_secuence(cr, uid, 'debit_note', False, printer.id, 'ecua.ndd', 'doc_number', context)
                    values['fecha_emision'] = time.strftime('%Y-%m-%d')
                    values['denominacion']='Nota de debito'
        return values
    
    

    def do_payment(self, cr, uid, ids, data, context=None):
        import pdb
        if context is None:
            context = {}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        journal_pool = self.pool.get('account.journal')
        period_pool = self.pool.get('account.period')
        timenow = time.strftime('%Y-%m-%d')
        for slip in self.browse(cr, uid, ids, context=context):
            journal_id = slip.journal_id.id
            move_line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            journal = journal_pool.browse(cr, uid, journal_id, context=context)
            if not slip.period_id:
                search_periods = period_pool.find(cr, uid, slip.date_to, context=context)
                period_id = search_periods[0]
            else:
                period_id = slip.period_id.id

            #default_partner_id = slip.employee_id.address_home_id.id
            #name = _('Payslip of %s') % (slip.partner_id.name) #employee_id
            name = ('Nota de Debito por %s') % (slip.ndc_concept)
            move = {
                'narration': name,
                'date': timenow,
                'ref': slip.doc_number,
                'journal_id': slip.journal_id.id,
                'period_id': period_id,
            }
            for line in slip.ndc_line_ids:
                amt_tax = 0.0
                amt = slip.valor_total and -line.valor_modifica or line.valor_modifica
                amtc = 0.0
                # partner_id = line.salary_rule_id.register_id.partner_id and line.salary_rule_id.register_id.partner_id.id or default_partner_id
                partner_id = slip.partner_id.id
                #debit_account_id = line.salary_rule_id.account_debit.id
                #credit_account_id = line.salary_rule_id.account_credit.id
                debit_account_id = slip.num_comprob_venta.account_id.id
                credit_account_id = slip.journal_id.default_debit_account_id.id
                for tax in line.invoice_line_tax_id:
                    pdb.set_trace()
                    amt_tax = tax.amount * amt
                    tax_debit_line = (0, 0, {
                    'name': line.motivo_modifica,
                    'date': timenow,
                    'partner_id': slip.partner_id.id,
                    'account_id': tax.account_paid_id.id,
                    #'account_id': debit_account_id,
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'debit': amt_tax > 0.0 and amt_tax or 0.0,
                    'credit': amt_tax < 0.0 and -amt_tax or 0.0,
                    #'analytic_account_id': line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or False,
                    'tax_code_id': tax.tax_code_id.id or False,
                    #'tax_code_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
                    'tax_amount': -amt_tax or 0.0,
                    #'tax_amount': line.salary_rule_id.account_tax_id and amt or 0.0,
                    })
                    move_line_ids.append(tax_debit_line)
                    debit_sum += tax_debit_line[2]['debit'] - tax_debit_line[2]['credit']
                    
                if debit_account_id:

                    debit_line = (0, 0, {
                    #'name': line.name,
                    'name': line.motivo_modifica,
                    'date': timenow,
                    'partner_id': slip.partner_id.id,
                    'account_id': debit_account_id,
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'debit': amt > 0.0 and amt or 0.0,
                    'credit': amt < 0.0 and -amt or 0.0,
                    #'analytic_account_id': line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or False,
                    #'tax_code_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,  
                    #'tax_amount': line.salary_rule_id.account_tax_id and amt or 0.0,
                })
                    move_line_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
                if credit_account_id:
                    amtc = debit_sum 
                    credit_line = (0, 0, {
                    #'name': line.name,
                    'name': line.motivo_modifica,
                    'date': timenow,
                    'partner_id': slip.partner_id.id,
                    'account_id': credit_account_id,
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'debit': amtc < 0.0 and -amtc or 0.0,
                    'credit': amtc > 0.0 and amtc or 0.0,
                    #'analytic_account_id': line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or False,
                    #'tax_code_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
                    #'tax_amount': line.salary_rule_id.account_tax_id and amt or 0.0,
                })
                    move_line_ids.append(credit_line)
                    credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
            if debit_sum > credit_sum:
                acc_id = slip.journal_id.default_credit_account_id.id
                if not acc_id:
                    raise osv.except_osv(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Credit Account!')%(slip.journal_id.name))
                adjust_credit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'date': timenow,
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'debit': 0.0,
                    'credit': debit_sum - credit_sum,
                })
                move_line_ids.append(adjust_credit)

            elif debit_sum < credit_sum:
                acc_id = slip.journal_id.default_debit_account_id.id
                if not acc_id:
                    raise osv.except_osv(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Debit Account!')%(slip.journal_id.name))
                adjust_debit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'date': timenow,
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'debit': credit_sum - debit_sum,
                    'credit': 0.0,
                })
                move_line_ids.append(adjust_debit)
            move.update({'line_id': move_line_ids})
            move_id = move_pool.create(cr, uid, move, context=context)
            pdb.set_trace()
            self.write(cr, uid, [slip.id], {'move_id': move_id, 'period_id' : period_id}, context=context)
            if slip.journal_id.entry_posted: 
                move_pool.post(cr, uid, [move_id], context=context) #omitir estado borrador
        self.write(cr, uid, ids, {'state':'posted'})
        return False

    def cancel_payment(self, cr, uid, ids, data, context=None):
        reconcile_pool = self.pool.get('account.move.reconcile')
        move_pool = self.pool.get('account.move')
        import pdb
        pdb.set_trace()
        for voucher in self.browse(cr, uid, ids, context=context):
            recs = []
            for line in voucher.move_ids:
                if line.reconcile_id:
                    recs += [line.reconcile_id.id]
                if line.reconcile_partial_id:
                    recs += [line.reconcile_partial_id.id]

            reconcile_pool.unlink(cr, uid, recs)

            if voucher.move_id:
                move_pool.button_cancel(cr, uid, [voucher.move_id.id])
                move_pool.unlink(cr, uid, [voucher.move_id.id])
        res = {
            'state':'cancel',
            'move_id':False,
        }
        self.write(cr, uid, ids, res)
        return True
    
    def action_cancel_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'draft'})
        return True

ecua_ndd_purchase()

class ecua_ndd_purchase_line(osv.osv):
    _name = 'ecua.ndd_line' 
    _description = 'Lineas de la Nota de debito'
    _columns = {
                'name':fields.char('Nombre', size=64, readonly=False),
                'ecua_ndd_id':fields.many2one('ecua.ndd.purchase','Nota'),
                'motivo_modifica':fields.char('Motivo', size=64,required=True),
                'valor_modifica':fields.float('Valor a modificar', required=True),
                'invoice_line_tax_id': fields.many2many('account.tax', 'account_invoice_line_tax_nd', 'invoice_line_id', 'tax_id', 'Taxes'),
                'iva12':fields.integer('IVA', readonly=True),
                'iva0':fields.integer('IVA', readonly=True),
                'valor_total':fields.float('Valor total'),                
                }
    
    def onchange_impuestos_ids(self, cr, uid, ids, comprobante_id, context=None):
        return True
    
    
    def calcula_ndd(self, cr, uid, ids, comprobante_id, context=None):
        return True
    
ecua_ndd_purchase_line()
