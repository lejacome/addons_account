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
import datetime
import re
import addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

class ecua_retencion(osv.osv):
    
    def check_retention_out(self,cr,uid,ids, context=None):
        cadena = '(\d{3})+\-(\d{3})+\-(\d{9})'
        for retention in self.browse(cr, uid, ids):
            ref = retention['doc_number']
            if retention['doc_number']:
                if re.match(cadena, ref):
                    return True
                else:
                    return False
            else:
                return True
    #valida autorizacion de las retenciones de venta        
    def validar_authorization(self,cr, uid, ids, context=None):
        a=0
        b= True
        for retention in self.browse(cr, uid, ids):
            if retention.authorization_sale:
                while (a<len(retention.authorization_sale)):
                    if(retention.authorization_sale[a]>='0' and retention.authorization_sale[a]<='9'):
                        a=a+1
                    else:
                        b=False
                        break
            return b
                    
    def check_ref(self, cr, uid, ids):
        partner_obj = self.pool.get('res.partner')
        for data in self.browse(cr, uid, ids):
            return partner_obj.check_ced(data.ruc).get('valid', False)
        
        
    def default_get(self, cr, uid, fields_list, context=None):
        #import pdb
        #pdb.set_trace()
        if context is None:
            context = {}
        doc_obj=self.pool.get('sri.type.document')
        values={}
        if not values:
            values={}
        curr_user = self.pool.get('res.users').browse(cr, uid, uid, context)
        values['ruc'] = curr_user.company_id.ruc
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
            auth_line_id = doc_obj.search(cr, uid, [('name','=','withholding'), ('printer_id','=',printer.id), ('state','=',True)])
            if not auth_line_id:
                raise osv.except_osv(_('Error!'), _('No existe autorización activa para generar retenciones'))
            if auth_line_id:
                auth_line = doc_obj.browse(cr, uid, auth_line_id[0],context)
                values['authorization_purchase_id'] = auth_line.sri_authorization_id.id
                values['autoriza_date_emision'] = auth_line.sri_authorization_id.start_date
                values['autoriza_date_expire'] = auth_line.sri_authorization_id.expiration_date
                values['doc_number'] = doc_obj.get_next_value_secuence(cr, uid, 'withholding', False, printer.id, 'ecua.retencion', 'doc_number', context)
                values['number_purchase']=values['doc_number']
                values['creation_date'] = time.strftime('%Y-%m-%d')
                values['transaction_type']='purchase'
                values['state']='draft'
        return values
        
            
    def _default_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id and user.company_id.id or False
    
    def _total(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for ret in self.browse(cr, uid, ids, context=context):
            val = 0.0
            cur = ret.invoice_id.currency_id
            for line in ret.retention_line_ids:
                if ret.transaction_type == 'purchase':
                    val += line.retained_value
                else:
                    val += line.retained_value_manual
            if cur:
                res[ret.id] = cur_obj.round(cr, uid, cur, val)
        return res

    def _total_iva(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for ret in self.browse(cr, uid, ids, context=context):
            val = 0.0
            cur = ret.invoice_id.currency_id
            for line in ret.retention_line_ids:
                if line.description == 'iva':
                    if ret.transaction_type == 'purchase':
                        val += line.retained_value
                    else:
                        val += line.retained_value_manual
            if cur:
                res[ret.id] = cur_obj.round(cr, uid, cur, val)
        return res

    def _total_renta(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for ret in self.browse(cr, uid, ids, context=context):            
            val = 0.0
            cur = ret.invoice_id.currency_id
            for line in ret.retention_line_ids:
                if line.description == 'renta':
                    if ret.transaction_type == 'purchase':
                        val += line.retained_value
                    else:
                        val += line.retained_value_manual
            if cur:
                res[ret.id] = cur_obj.round(cr, uid, cur, val)
        return res
    
    def _get_retention(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('ecua.retencion.line').browse(cr, uid, ids, context=context):
            result[line.retention_id.id] = True
        return result.keys()
    
    def _get_generated_document(self, cr, uid, ids, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id.generate_automatic
    
    _name = 'ecua.retencion'
    _description='Retention'
        
    _columns = {                 
        'doc_number': fields.char('Number', size=17, required=False, states={'approved':[('readonly',True)]}),
        'number_purchase': fields.char('Retention Number', size=17, required=False, states={'approved':[('readonly',True)], 'canceled':[('readonly',True)]}),
        'number_sale': fields.char('Retention Number', size=17, required=False, states={'approved':[('readonly',True)], 'canceled':[('readonly',True)]}),
        'creation_date': fields.date('Creation Date',states={'approved':[('readonly',True)], 'canceled':[('readonly',True)]}),
        'authorization_purchase_id':fields.many2one('sri.authorization', 'Authorization', required=False, readonly=True),
        'authorization_sale_id':fields.many2one('sri.authorization.supplier', 'Authorization', ),
        'authorization_sale':fields.char('Authorization', size=10, required=False, readonly=False, states={'approved':[('readonly',True)], 'canceled':[('readonly',True)]}, help='This Number is necesary for SRI reports'),
        'autoriza_date_emision':fields.date('Fecha emision', readonly=True),
        'autoriza_date_expire':fields.date('Fecha caducidad', readonly=True),        
        'transaction_type':fields.selection([
            ('purchase','Compras'),
            ('sale','Ventas'),
            ],  'Transaction type', required=True),
        'retention_line_ids': fields.one2many('ecua.retencion.line', 'retention_id', 'Retention Lines',states={'approved':[('readonly',True)], 'canceled':[('readonly',True)]}),   
        'invoice_id': fields.many2one('account.invoice', 'Number of document', required=False, states={'approved':[('readonly',True)], 'canceled':[('readonly',True)]}, ondelete='cascade'),
        'partner_id': fields.related('invoice_id','partner_id', type='many2one', relation='res.partner', string='Partner', store=True), 
        'company_id': fields.related('invoice_id','company_id', type='many2one', relation='res.company', string='Company', store=True),
        'state':fields.selection([
            ('draft','Draft'),
            ('approved','Approved'),
            ('canceled','Canceled'),
            ],  'State', required=True),
        'total': fields.function(_total, method=True, type='float', string='Total Retenido', store = {
                                 'ecua.retencion': (lambda self, cr, uid, ids, c={}: ids, ['retention_line_ids'], 11),
                                 'ecua.lineas.retencion': (_get_retention, ['tax_base', 'retention_percentage', 'retained_value',], 11),
                                 }), 
        'total_iva': fields.function(_total_iva, method=True, type='float', string='Total IVA', store = {
                                 'ecua.retencion': (lambda self, cr, uid, ids, c={}: ids, ['retention_line_ids'], 11),
                                 'ecua.lineas.retencion': (_get_retention, ['tax_base', 'retention_percentage', 'retained_value',], 11),
                                 }), 
        'total_renta': fields.function(_total_renta, method=True, type='float', string='Total Renta', store = {
                                 'ecua.retencion': (lambda self, cr, uid, ids, c={}: ids, ['retention_line_ids'], 11),
                                 'ecua.lineas.retencion': (_get_retention, ['tax_base', 'retention_percentage', 'retained_value',], 11),
                                 }),
        'account_voucher_ids':fields.one2many('account.voucher', 'retention_id', 'Retention', required=False),
        'automatic':fields.boolean('Automatic?',),
        'period_id': fields.related('invoice_id','period_id', type='many2one', relation='account.period', string='Period', store=True), 
        'shop_id':fields.many2one('sale.shop', 'Shop', readonly=True, states={'draft':[('readonly',False)]}),
        'printer_id':fields.many2one('sri.printer.point', 'Printer Point', readonly=True, states={'draft':[('readonly',False)]}),             
             }

    _rec_name='doc_number'
    
    _constraints = [(check_retention_out, _('El numero de retencion es incorrecto, debe ser como 001-00X-000XXXXXX, X es un numero'),['number']),]
    
    _sql_constraints = [('retencion_compra_unico','unique(number_purchase, company_id)', _('Hay otra Retencion generado con este número, por favor verifique'))]
    
    _defaults = {
                 'doc_number': '',
                 'transaction_type': lambda *a: 'sale',
                 'state': 'draft',
                 }

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        retention = self.pool.get('ecua.retencion').browse(cr, uid, ids, context)
        flag = context.get('invoice', False)
        unlink_ids = []
        for r in retention:
            if not flag:
                if r['state'] == 'draft':
                    unlink_ids.append(r['id'])
                else:
                    if r['state'] == 'canceled':
                        if r['transaction_type'] == 'sale':
                            unlink_ids.append(r['id'])
                        else:
                            raise osv.except_osv(_('Invalid action !'), _('Cannot delete retention(s) that are already assigned Number!'))
            else:
                unlink_ids.append(r['id'])
        return super(ecua_retencion, self).unlink(cr, uid, unlink_ids, context)
    
    
    def action_move_line_create(self, cr, uid, ids, context=None):

        def _get_payment_term_lines(term_id, amount):
            term_pool = self.pool.get('account.payment.term')
            if term_id and amount:
                terms = term_pool.compute(cr, uid, term_id, amount)
                return terms
            return False
        if context is None:
            context = {}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        currency_pool = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        seq_obj = self.pool.get('ir.sequence')
        for inv in self.pool.get('account.voucher').browse(cr, uid, ids, context=context):
            if inv.move_id:
                continue
            context_multi_currency = context.copy()
            context_multi_currency.update({'date': inv.date})

            if inv.number:
                name = inv.number
            elif inv.journal_id.sequence_id:
                name = seq_obj.get_id(cr, uid, inv.journal_id.sequence_id.id)
            else:
                raise osv.except_osv(_('Error !'), _('Please define a sequence on the journal !'))
            if not inv.reference:
                ref = name.replace('/','')
            else:
                ref = inv.reference

            move = {
                'name': name,
                'journal_id': inv.journal_id.id,
                'narration': inv.narration,
                'date': inv.date,
                'ref': ref,
                'period_id': inv.period_id and inv.period_id.id or False
            }
            move_id = move_pool.create(cr, uid, move)

            #create the first line manually
            company_currency = inv.journal_id.company_id.currency_id.id
            current_currency = inv.currency_id.id
            debit = 0.0
            credit = 0.0
            # TODO: is there any other alternative then the voucher type ??
            # -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
            if inv.type in ('purchase', 'payment'):
                credit = currency_pool.compute(cr, uid, current_currency, company_currency, inv.amount, context=context_multi_currency)
            elif inv.type in ('sale', 'receipt'):
                debit = currency_pool.compute(cr, uid, current_currency, company_currency, inv.amount, context=context_multi_currency)
            if debit < 0:
                credit = -debit
                debit = 0.0
            if credit < 0:
                debit = -credit
                credit = 0.0
            sign = debit - credit < 0 and -1 or 1
            #create the first line of the voucher
            #TODO: se debe especificar el codigo de impuesto para la realizacion del informe de impuestos
            tax_code_obj = self.pool.get('account.tax.code')
            move_line = {}
            try:
                if context['tax']=='iva':
                    move_line = {
                        'name': inv.name or '/',
                        'debit': debit,
                        'credit': credit,
                        'account_id': inv.account_id.id,
                        'move_id': move_id,
                        'journal_id': inv.journal_id.id,
                        'period_id': inv.period_id.id,
                        'partner_id': inv.partner_id.id,
                        'currency_id': company_currency <> current_currency and  current_currency or False,
                        'amount_currency': company_currency <> current_currency and sign * inv.amount or 0.0,
                        'date': inv.date,
                        'date_maturity': inv.date_due,
                    }
                elif context['tax']=='renta':
                    move_line = {
                        'name': inv.name or '/',
                        'debit': debit,
                        'credit': credit,
                        'account_id': inv.account_id.id,
                        'move_id': move_id,
                        'journal_id': inv.journal_id.id,
                        'period_id': inv.period_id.id,
                        'partner_id': inv.partner_id.id,
                        'currency_id': company_currency <> current_currency and  current_currency or False,
                        'amount_currency': company_currency <> current_currency and sign * inv.amount or 0.0,
                        'date': inv.date,
                        'date_maturity': inv.date_due,
                    }
            except:
                raise osv.except_osv('Error!', _("The residual value of invoice is lower than total value of withholding"))
            move_line_pool.create(cr, uid, move_line)
            rec_list_ids = []
            line_total = debit - credit
            if inv.type == 'sale':
                line_total = line_total - currency_pool.compute(cr, uid, inv.currency_id.id, company_currency, inv.tax_amount, context=context_multi_currency)
            elif inv.type == 'purchase':
                line_total = line_total + currency_pool.compute(cr, uid, inv.currency_id.id, company_currency, inv.tax_amount, context=context_multi_currency)

            for line in inv.line_ids:
                #create one move line per voucher line where amount is not 0.0
                if not line.amount:
                    continue
                #we check if the voucher line is fully paid or not and create a move line to balance the payment and initial invoice if needed
                if line.amount == line.amount_unreconciled:
                    amount = line.move_line_id.amount_residual #residual amount in company currency
                else:
                    amount = currency_pool.compute(cr, uid, current_currency, company_currency, line.untax_amount or line.amount, context=context_multi_currency)
                move_line = {
                    'journal_id': inv.journal_id.id,
                    'period_id': inv.period_id.id,
                    'name': line.name and line.name or '/',
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'partner_id': inv.partner_id.id,
                    'currency_id': company_currency <> current_currency and current_currency or False,
                    'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': 0.0,
                    'date': inv.date
                }
                #print 'Por cada linea del voucher'
                #print move_line
                if amount < 0:
                    amount = -amount
                    if line.type == 'dr':
                        line.type = 'cr'
                    else:
                        line.type = 'dr'

                if (line.type=='dr'):
                    line_total += amount
                    move_line['debit'] = amount
                else:
                    line_total -= amount
                    move_line['credit'] = amount

                if inv.tax_id and inv.type in ('sale', 'purchase'):
                    move_line.update({
                        'account_tax_id': inv.tax_id.tax_code_id.id,
                    })
                if move_line.get('account_tax_id', False):
                    tax_data = tax_obj.browse(cr, uid, [move_line['account_tax_id']], context=context)[0]
                    if not (tax_data.base_code_id and tax_data.tax_code_id):
                        raise osv.except_osv(_('No Account Base Code and Account Tax Code!'),_("You have to configure account base code and account tax code on the '%s' tax!") % (tax_data.name))
                sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                move_line['amount_currency'] = company_currency <> current_currency and sign * line.amount or 0.0
                voucher_line = move_line_pool.create(cr, uid, move_line)
                if line.move_line_id.id:
                    rec_ids = [voucher_line, line.move_line_id.id]
                    rec_list_ids.append(rec_ids)

            if not currency_pool.is_zero(cr, uid, inv.currency_id, line_total):
                diff = line_total
                account_id = False
                if inv.payment_option == 'with_writeoff':
                    account_id = inv.writeoff_acc_id.id
                elif inv.type in ('sale', 'receipt'):
                    #account_id = inv.partner_id.property_account_receivable.id
                    account_id = inv.journal_id.default_debit_account_id.id
                else:
                    #account_id = inv.partner_id.property_account_payable.id
                    account_id = inv.journal_id.default_credit_account_id.id
                move_line = {
                    'name': name,
                    'account_id': account_id,
                    'move_id': move_id,
                    'partner_id': inv.partner_id.id,
                    'date': inv.date,
                    'credit': diff > 0 and diff or 0.0,
                    'debit': diff < 0 and -diff or 0.0,
                    #'amount_currency': company_currency <> current_currency and currency_pool.compute(cr, uid, company_currency, current_currency, diff * -1, context=context_multi_currency) or 0.0,
                    #'currency_id': company_currency <> current_currency and current_currency or False,
                }
                move_line_pool.create(cr, uid, move_line)
                #print 'asiento con desajuste'
                #print move_line
            self.pool.get('account.voucher').write(cr, uid, [inv.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            move_pool.post(cr, uid, [move_id], context={})
            for rec_ids in rec_list_ids:
                if len(rec_ids) >= 2:
                    move_line_pool.reconcile_partial(cr, uid, rec_ids)
        return True

    def crear_asiento_enventas(self,cr,uid,ids,ret,context=None):
        ret_line_obj = self.pool.get('ecua.retencion.line')
        ret_obj = self.pool.get('ecua.retencion')
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        journal_iva = company.journal_iva_id
        journal_ir = company.journal_ir_id      
        #import pdb
        #pdb.set_trace()
        for retention in ret_obj.search(cr, uid, [('invoice_id.partner_id.id', '=', ret.invoice_id.partner_id.id), ('transaction_type','=','sale'), ('id','not in',tuple(ids))]):
            if ret_obj.browse(cr, uid, [retention,], context)[0].number_sale == ret.number_sale:
                raise osv.except_osv(_('Error!'), _("There is an retention with number %s of client %s") % (ret.number_sale, ret.invoice_id.partner_id.name))                                        
                #se comprueba que la factura se encuentre abierta
        if not ret.invoice_id.state == 'open':
            raise osv.except_osv('Error!', "The invoice is not open, you cannot add a retention")
                #Se verifica que el residuo de la factura no sea superior a lo que se va a retener
        if ret.invoice_id.residual < ret.total:
            raise osv.except_osv('Error!', "The residual value of invoice is lower than total value of withholding")
                #Obtengo el periodo de la factura
        period=ret.invoice_id.period_id.id                                
                #Obtenemos las lineas de la retencion
        line_ids = ret_line_obj.search(cr, uid, [('retention_id', '=', ret['id']),])
        lines = ret_line_obj.browse(cr, uid, line_ids, context)
                
                #variable que guarda los ids de los voucher que se crean para su posterior uso desde retencion
        move_line_ir = []
        move_line_iva = []
                #verifico que existan lineas de retencion            
        if lines:
            #Definimos cual sera la cabecera de las retenciones de iva                
            name_iva = ('Retencion al IVA en ventas')
            move_iva = {
                        'narration': name_iva,
                        'date': ret.creation_date,
                        'ref': ret.number_purchase,
                        'journal_id': journal_iva.id,
                        'period_id': period,
                        }
            #Definimos cual sera la cabecera de las retenciones de renta
            name_ir = ('Retencion al IR en ventas')
            move_ir = {
                        'narration': name_ir,
                        'date': ret.creation_date,
                        'ref': ret.number_purchase,
                        'journal_id': journal_ir.id,
                        'period_id': period,
                        }                                
                   
                    #recorro cada linea de retencion
                    #variables de control para verificar que existen lineas de cada tipo
            renta = False
            iva = False
            debit_sum=credit_sum=credit_sum_ir=debit_sum_ir=0.0
            for line in lines:
                amt = line.retained_value
                #verifico las lineas por tipo para seleccionar el diario correspondiente
                if line.description == 'iva':
                    debit_account_id_iva1=line.tax_id.account_collected_id #% de IVA cobrado en la Retencion
                    if ret.invoice_id.tax_line:
                        debit_account_id_iva2= ret.invoice_id.tax_line[0].account_id#  % de Impuesto cobrado en ventas
                        #if ret.invoice_id.tax_line[1]: #Si tiene mas de un impuesto tendremos que realizar la retencion manualmente...xq no sabria con que diario hacer los moviemientos
                        #    raise osv.except_osv(_('Error!'),_('La factura tiene mas de un impuesto, realice la rentención manualmente!. FAC: %s' )%(ret.invoice_id.invoice_number))                            
                    else:
                        raise osv.except_osv(_('Error!'), _("La factura no tiene un impuesto, revise la factura %s!")%(ret.invoice_id.invoice_number))                                        
                    credit_account_id_iva1=journal_iva.default_credit_account_id #Iva pagado en retenciones
                    credit_account_id_iva2=ret.invoice_id.account_id #Cuentas y documentos por cobrar                                                    
                    if debit_account_id_iva1:
                        vals_iva_line = (0, 0, {
                                    'name': debit_account_id_iva1.name,
                                    'date': ret.creation_date,
                                    'partner_id': ret.partner_id.id,
                                    'account_id': debit_account_id_iva1.id,
                                    'journal_id': journal_iva.id,
                                    'period_id': period,
                                    'debit': amt > 0.0 and amt or 0.0,
                                    'credit': amt < 0.0 and -amt or 0.0,
                                    'tax_code_id': line.tax_id.tax_code_id.id or False,                                    
                                    'tax_amount': amt or 0.0,
                                    })
                        move_line_iva.append(vals_iva_line)
                        debit_sum += vals_iva_line[2]['debit'] - vals_iva_line[2]['credit']
                    if credit_account_id_iva1:                                
                        vals_iva_line = (0, 0, {
                                    'name': credit_account_id_iva1.name,
                                    'date': ret.creation_date,
                                    'partner_id': ret.partner_id.id,
                                    'account_id': credit_account_id_iva1.id,
                                    'journal_id': journal_iva.id,
                                    'period_id': period,
                                    'debit': amt < 0.0 and -amt or 0.0,
                                    'credit': amt > 0.0 and amt or 0.0,                                    
                                    'tax_code_id': line.tax_id.tax_code_id.id or False,                                    
                                    'tax_amount': amt or 0.0,                                    
                                    })
                        move_line_iva.append(vals_iva_line)
                        credit_sum += vals_iva_line[2]['credit'] - vals_iva_line[2]['debit']
                    if debit_account_id_iva2:
                        vals_iva_line = (0, 0, {
                                    'name': debit_account_id_iva2.name,
                                    'date': ret.creation_date,
                                    'partner_id': ret.partner_id.id,
                                    'account_id': debit_account_id_iva2.id,
                                    'journal_id': journal_iva.id,
                                    'period_id': period,
                                    'debit': amt > 0.0 and amt or 0.0,
                                    'credit': amt < 0.0 and -amt or 0.0,
                                    'tax_code_id': line.tax_id.tax_code_id.id or False,                                    
                                    'tax_amount': amt or 0.0,
                                    })
                        move_line_iva.append(vals_iva_line)
                        debit_sum += vals_iva_line[2]['debit'] - vals_iva_line[2]['credit']
                    if credit_account_id_iva2:                                
                        vals_iva_line = (0, 0, {
                                    'name': credit_account_id_iva2.name,
                                    'date': ret.creation_date,
                                    'partner_id': ret.partner_id.id,
                                    'account_id': credit_account_id_iva2.id,
                                    'journal_id': journal_iva.id,
                                    'period_id': period,
                                    'debit': amt < 0.0 and -amt or 0.0,
                                    'credit': amt > 0.0 and amt or 0.0,                                    
                                    'tax_code_id': line.tax_id.tax_code_id.id or False,                                    
                                    'tax_amount': amt or 0.0,                                    
                                    })
                        move_line_iva.append(vals_iva_line)
                        credit_sum += vals_iva_line[2]['credit'] - vals_iva_line[2]['debit']
                            #se cambia el valor de la variable ya que se encontro al menos una linea de retencion
                        iva = True                            
                if line.description == 'renta':
                    debit_account_id_ir1=journal_iva.default_debit_account_id
                    debit_account_id_ir2=ret.invoice_id.journal_id.default_debit_account_id
                    credit_account_id_ir1=line.tax_id.account_collected_id
                    credit_account_id_ir2=ret.invoice_id.account_id  
                    if debit_account_id_ir1:                    
                        vals_ir_line = (0, 0, {
                                    'name': debit_account_id_ir1.name,
                                    'date': ret.creation_date,
                                    'partner_id': ret.partner_id.id,
                                    'account_id': debit_account_id_ir1.id,
                                    'journal_id': journal_ir.id,
                                    'period_id': period,
                                    'debit': amt > 0.0 and amt or 0.0,
                                    'credit': amt < 0.0 and -amt or 0.0,                                    
                                    'tax_code_id': line.tax_id.tax_code_id.id or False,                                    
                                    'tax_amount': amt or 0.0,                                    
                                    })
                        move_line_ir.append(vals_ir_line)
                        debit_sum_ir += vals_ir_line[2]['debit'] - vals_ir_line[2]['credit']
                    if credit_account_id_ir1:                    
                        vals_ir_line = (0, 0, {
                                    'name': credit_account_id_ir1.name,
                                    'date': ret.creation_date,
                                    'partner_id': ret.partner_id.id,
                                    'account_id': credit_account_id_ir1.id,
                                    'journal_id': journal_ir.id,
                                    'period_id': period,
                                    'debit': amt < 0.0 and -amt or 0.0,
                                    'credit': amt > 0.0 and amt or 0.0,                                    
                                    'tax_code_id': line.tax_id.tax_code_id.id or False,                                    
                                    'tax_amount': amt or 0.0,                                    
                                    })
                        move_line_ir.append(vals_ir_line)
                        credit_sum_ir += vals_ir_line[2]['credit'] - vals_ir_line[2]['debit']
                    if debit_account_id_ir2:                    
                        vals_ir_line = (0, 0, {
                                    'name': debit_account_id_ir2.name,
                                    'date': ret.creation_date,
                                    'partner_id': ret.partner_id.id,
                                    'account_id': debit_account_id_ir2.id,
                                    'journal_id': journal_ir.id,
                                    'period_id': period,
                                    'debit': amt > 0.0 and amt or 0.0,
                                    'credit': amt < 0.0 and -amt or 0.0,                                    
                                    'tax_code_id': line.tax_id.tax_code_id.id or False,                                    
                                    'tax_amount': amt or 0.0,                                    
                                    })
                        move_line_ir.append(vals_ir_line)
                        debit_sum_ir += vals_ir_line[2]['debit'] - vals_ir_line[2]['credit']
                    if credit_account_id_ir2:                    
                        vals_ir_line = (0, 0, {
                                    'name': credit_account_id_ir2.name,
                                    'date': ret.creation_date,
                                    'partner_id': ret.partner_id.id,
                                    'account_id': credit_account_id_ir2.id,
                                    'journal_id': journal_ir.id,
                                    'period_id': period,
                                    'debit': amt < 0.0 and -amt or 0.0,
                                    'credit': amt > 0.0 and amt or 0.0,                                    
                                    'tax_code_id': line.tax_id.tax_code_id.id or False,                                    
                                    'tax_amount': amt or 0.0,                                    
                                    })
                        move_line_ir.append(vals_ir_line)
                        credit_sum_ir += vals_ir_line[2]['credit'] - vals_ir_line[2]['debit']
                                #se cambia el valor de la variable ya que se encontro al menos una linea de retencion
                        renta = True
                if debit_sum > credit_sum:
                    acc_id = journal_iva.default_credit_account_id.id
                    if not acc_id:
                        raise osv.except_osv(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Credit Account!')%(journal_iva.name))
                    adjust_credit = (0, 0, {
                                'name': _('Adjustment Entry'),
                                'date': ret.creation_date,
                                'partner_id': False,
                                'account_id': acc_id,
                                'journal_id': journal_iva.id,
                                'period_id': period,
                                'debit': 0.0,
                                'credit': debit_sum - credit_sum,
                            })
                    move_line_iva.append(adjust_credit)
                    acc_id = journal_ir.default_credit_account_id.id
                elif debit_sum_ir > credit_sum_ir:
                    if not acc_id:
                        raise osv.except_osv(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Credit Account!')%(journal_ir.name))
                    adjust_credit_ir = (0, 0, {
                                'name': _('Adjustment Entry'),
                                'date': ret.creation_date,
                                'partner_id': False,
                                'account_id': acc_id,
                                'journal_id': journal_ir.id,
                                'period_id': period,
                                'debit': 0.0,
                                'credit': debit_sum_ir - credit_sum_ir,
                            })
                    move_line_ir.append(adjust_credit_ir)
            
                elif debit_sum < credit_sum:
                    acc_id = journal_iva.default_debit_account_id.id
                    if not acc_id:
                        raise osv.except_osv(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Debit Account!')%(journal_iva.name))
                    adjust_debit = (0, 0, {
                                'name': _('Adjustment Entry'),
                                'date': ret.creation_date,
                                'partner_id': False,
                                'account_id': acc_id,
                                'journal_id': journal_iva.id,
                                'period_id': period,
                                'debit': credit_sum - debit_sum,
                                'credit': 0.0,
                            })
                    move_line_iva.append(adjust_debit)
                    acc_id = journal_ir.default_debit_account_id.id
                elif debit_sum_ir < credit_sum_ir: 
                    if not acc_id:
                        raise osv.except_osv(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Debit Account!')%(journal_ir.name))
                    adjust_debit = (0, 0, {
                                'name': _('Adjustment Entry'),
                                'date': ret.creation_date,
                                'partner_id': False,
                                'account_id': acc_id,
                                'journal_id': journal_ir.id,
                                'period_id': period,
                                'debit': credit_sum_ir - debit_sum_ir,
                                'credit': 0.0,
                            })
                    move_line_ir.append(adjust_debit)
                if iva == True:
                    acc_move_obj = self.pool.get('account.move')    
                    move_iva.update({'line_id': move_line_iva})
                    move_id_iva = acc_move_obj.create(cr, uid, move_iva, context=context)
                    self.write(cr, uid, [ret.id], {'move_id': move_id_iva, 'period_id' : period}, context=context)
                    if journal_iva.entry_posted: 
                        acc_move_obj.post(cr, uid, [move_id_iva], context=context) #omitir estado borrador
                elif renta == True:                           
                    acc_move_obj1= self.pool.get('account.move')            
                    move_ir.update({'line_id': move_line_ir})
                    move_id_ir = acc_move_obj1.create(cr, uid, move_ir, context=context)                        
                    self.write(cr, uid, [ret.id], {'move_id': move_id_ir, 'period_id' : period}, context=context)                
                    if journal_ir.entry_posted:
                        acc_move_obj1.post(cr, uid, [move_id_ir], context=context) #omitir estado borrador
            self.write(cr, uid, ids, {'state': 'approved'})
            return False
    
    def crear_asiento_encompras(self,cr,uid,ids,ret,context=None):
        ret_line_obj = self.pool.get('ecua.retencion.line')
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id        
        journal_iva = company.journal_iva_id
        journal_ir = company.journal_ir_id    
        #se comprueba que la factura se encuentre abierta
        if not ret.invoice_id.state == 'open':
            raise osv.except_osv('Error!', "The invoice is not open, you cannot add a retention")
                #Se verifica que el residuo de la factura no sea superior a lo que se va a retener
        if ret.invoice_id.residual < ret.total:
            raise osv.except_osv('Error!', "The residual value of invoice is lower than total value of retention")
                #Obtengo el periodo de la factura
        period=ret.invoice_id.period_id.id                                
                #Obtenemos las lineas de la retencion
        line_ids = ret_line_obj.search(cr, uid, [('retention_id', '=', ret['id']),])
        lines = ret_line_obj.browse(cr, uid, line_ids, context)
                
        #variable que guarda los ids de los voucher que se crean para su posterior uso desde retencion
        move_line_ir = []
        move_line_iva = []
        #verifico que existan lineas de retencion
                
        if lines:
            #Definimos cual sera la cabecera de las retenciones de iva                
            name_iva = ('Retencion al IVA en compras') #en este caso de compras
            move_iva = {
                        'narration': name_iva,
                        'date': ret.creation_date,
                        'ref': ret.number_purchase,
                        'journal_id': journal_iva.id,
                        'period_id': period,
                        }
            #Definimos cual sera la cabecera de las retenciones de renta
            name_ir = ('Retencion al IR en compras') #en este caso de compras
            move_ir = {
                        'narration': name_ir,
                        'date': ret.creation_date,
                        'ref': ret.number_purchase,
                        'journal_id': journal_ir.id,
                        'period_id': period,
                        }                                
                   
                    #recorro cada linea de retencion
                    #variables de control para verificar que existen lineas de cada tipo
            renta = False
            iva = False
            debit_sum=credit_sum=credit_sum_ir=debit_sum_ir=0.0
            for line in lines:
                amt = line.retained_value
                #verifico las lineas por tipo para seleccionar el diario correspondiente
                #import pdb
                #pdb.set_trace()
                if line.description == 'iva':
                    credit_account_id_iva1=line.tax_id.account_collected_id #Retencion del x% en el iva 
                    #SACAMOS EL IMPUESTO DE LA FACTURA DE LA LISTA DE INPUESTOS DE tax_line
                    if ret.invoice_id.tax_line:
                        credit_account_id_iva2= ret.invoice_id.tax_line[0].account_id#Otros --Impuestos
                        #if ret.invoice_id.tax_line[1]: #Si tiene mas de un impuesto tendremos que realizar la retencion manualmente...xq no sabria con que diario hacer los moviemientos
                        #    raise osv.except_osv(_('Error!'),_('La factura tiene mas de un impuesto, realice la rentención manualmente!. FAC: %s' )%(ret.invoice_id.invoice_number))                            
                    else:
                        raise osv.except_osv(_('Error!'), _("La factura no tiene un impuesto, revise la factura %s!")%(ret.invoice_id.invoice_number))                         
                    debit_account_id_iva1=journal_iva.default_credit_account_id #IVA pagado en retenciones a la fuente ok
                    debit_account_id_iva2=ret.invoice_id.account_id #Cuentas y Documentos por pagar
                    if debit_account_id_iva1:
                        vals_iva_line1 = (0, 0, {
                                        'name': debit_account_id_iva1.name,
                                        'date': ret.creation_date,
                                        'partner_id': ret.partner_id.id,
                                        'account_id': debit_account_id_iva1.id,
                                        'journal_id': journal_iva.id,
                                        'period_id': period,
                                        'debit': amt > 0.0 and amt or 0.0,
                                        'credit': amt < 0.0 and -amt or 0.0,                                    
                                        'tax_code_id': line.tax_id.tax_code_id.id or False,
                                        'tax_amount': amt or 0.0,
                                        })
                        move_line_iva.append(vals_iva_line1)
                        debit_sum += vals_iva_line1[2]['debit'] - vals_iva_line1[2]['credit']
                    if credit_account_id_iva1:
                        vals_iva_line2 = (0, 0, {
                                        'name': credit_account_id_iva1.name,
                                        'date': ret.creation_date,
                                        'partner_id': ret.partner_id.id,
                                        'account_id': credit_account_id_iva1.id,
                                        'journal_id': journal_iva.id,
                                        'period_id': period,
                                        'debit': amt < 0.0 and -amt or 0.0,
                                        'credit': amt > 0.0 and amt or 0.0,                                     
                                        'tax_code_id': line.tax_id.tax_code_id.id or False,                                    
                                        'tax_amount': amt or 0.0,                                    
                                        })
                        move_line_iva.append(vals_iva_line2)
                        credit_sum += vals_iva_line2[2]['credit'] - vals_iva_line2[2]['debit']
                    if debit_account_id_iva2:
                        vals_iva_line3 = (0, 0, {
                                        'name': debit_account_id_iva2.name,
                                        'date': ret.creation_date,
                                        'partner_id': ret.partner_id.id,
                                        'account_id': debit_account_id_iva2.id,
                                        'journal_id': journal_iva.id,
                                        'period_id': period,
                                        'debit': amt > 0.0 and amt or 0.0,
                                        'credit': amt < 0.0 and -amt or 0.0,                                     
                                        'tax_code_id': line.tax_id.tax_code_id.id or False,
                                        'tax_amount': amt or 0.0,
                                        })
                        move_line_iva.append(vals_iva_line3)
                        debit_sum += vals_iva_line3[2]['debit'] - vals_iva_line3[2]['credit']
                    if credit_account_id_iva2:
                        vals_iva_line4 = (0, 0, {
                                        'name': credit_account_id_iva2.name,
                                        'date': ret.creation_date,
                                        'partner_id': ret.partner_id.id,
                                        'account_id': credit_account_id_iva2.id,
                                        'journal_id': journal_iva.id,
                                        'period_id': period,
                                        'debit': amt < 0.0 and -amt or 0.0,
                                        'credit': amt > 0.0 and amt or 0.0,                                    
                                        'tax_code_id': line.tax_id.tax_code_id.id or False,                                    
                                        'tax_amount': amt or 0.0,                                    
                                        })
                        move_line_iva.append(vals_iva_line4)
                        credit_sum += vals_iva_line4[2]['credit'] - vals_iva_line4[2]['debit']
                                #se cambia el valor de la variable ya que se encontro al menos una linea de retencion
                        iva = True                           
                
                if line.description == 'renta':
                    debit_account_id_ir1=journal_ir.default_credit_account_id#IR pagado en retenciones a la fuente ok
                    debit_account_id_ir2=ret.invoice_id.account_id #Cuentas y Documentos por pagar
                    credit_account_id_ir1=line.tax_id.account_collected_id #Porcentaje retenido en impuesto a la rente
                    credit_account_id_ir2=ret.invoice_id.journal_id.default_credit_account_id #Otros (compras de mercaderia)
                    if debit_account_id_ir1:
                        vals_ir_line1 = (0, 0, {
                                    'name': debit_account_id_ir1.name,
                                    'date': ret.creation_date,
                                    'partner_id': ret.partner_id.id,
                                    'account_id': debit_account_id_ir1.id,
                                    'journal_id': journal_ir.id,
                                    'period_id': period,
                                    'debit': amt > 0.0 and amt or 0.0,
                                    'credit': amt < 0.0 and -amt or 0.0,                                    
                                    'tax_code_id': line.tax_id.tax_code_id.id or False,                                    
                                    'tax_amount': amt or 0.0,                                    
                                    })
                        move_line_ir.append(vals_ir_line1)
                        debit_sum_ir += vals_ir_line1[2]['debit'] - vals_ir_line1[2]['credit']
                    if credit_account_id_ir1:
                        vals_ir_line2 = (0, 0, {
                                    'name': credit_account_id_ir1.name,
                                    'date': ret.creation_date,
                                    'partner_id': ret.partner_id.id,
                                    'account_id': credit_account_id_ir1.id,
                                    'journal_id': journal_ir.id,
                                    'period_id': period,
                                    'debit': amt < 0.0 and -amt or 0.0,
                                    'credit': amt > 0.0 and amt or 0.0,                                    
                                    'tax_code_id': line.tax_id.tax_code_id.id or False,                                    
                                    'tax_amount': amt or 0.0,                                    
                                    })
                        move_line_ir.append(vals_ir_line2)
                        credit_sum_ir += vals_ir_line2[2]['credit'] - vals_ir_line2[2]['debit']
                    if debit_account_id_ir2:
                        vals_ir_line3 = (0, 0, {
                                    'name': debit_account_id_ir2.name,
                                    'date': ret.creation_date,
                                    'partner_id': ret.partner_id.id,
                                    'account_id': debit_account_id_ir2.id,
                                    'journal_id': journal_ir.id,
                                    'period_id': period,
                                    'debit': amt > 0.0 and amt or 0.0,
                                    'credit': amt < 0.0 and -amt or 0.0,                                    
                                    'tax_code_id': line.tax_id.tax_code_id.id or False,                                    
                                    'tax_amount': amt or 0.0,                                    
                                    })
                        move_line_ir.append(vals_ir_line3)
                        debit_sum_ir += vals_ir_line3[2]['debit'] - vals_ir_line3[2]['credit']
                    if credit_account_id_ir2:
                        vals_ir_line4 = (0, 0, {
                                    'name': credit_account_id_ir2.name,
                                    'date': ret.creation_date,
                                    'partner_id': ret.partner_id.id,
                                    'account_id': credit_account_id_ir2.id,
                                    'journal_id': journal_ir.id,
                                    'period_id': period,
                                    'debit': amt < 0.0 and -amt or 0.0,
                                    'credit': amt > 0.0 and amt or 0.0,                                    
                                    'tax_code_id': line.tax_id.tax_code_id.id or False,                                    
                                    'tax_amount': amt or 0.0,                                    
                                    })
                        move_line_ir.append(vals_ir_line4)
                        credit_sum_ir += vals_ir_line4[2]['credit'] - vals_ir_line4[2]['debit']
                                #se cambia el valor de la variable ya que se encontro al menos una linea de retencion
                        renta = True
                if debit_sum > credit_sum:
                    acc_id = journal_iva.default_credit_account_id.id
                    if not acc_id:
                        raise osv.except_osv(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Credit Account!')%(journal_iva.name))
                    adjust_credit = (0, 0, {
                                'name': _('Adjustment Entry'),
                                'date': ret.creation_date,
                                'partner_id': False,
                                'account_id': acc_id,
                                'journal_id': journal_iva.id,
                                'period_id': period,
                                'debit': 0.0,
                                'credit': debit_sum - credit_sum,
                            })
                    move_line_iva.append(adjust_credit)
                elif debit_sum_ir > credit_sum_ir:
                    acc_id = journal_ir.default_credit_account_id.id
                    if not acc_id:
                        raise osv.except_osv(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Credit Account!')%(journal_ir.name))
                    adjust_credit_ir = (0, 0, {
                                'name': _('Adjustment Entry'),
                                'date': ret.creation_date,
                                'partner_id': False,
                                'account_id': acc_id,
                                'journal_id': journal_ir.id,
                                'period_id': period,
                                'debit': 0.0,
                                'credit': debit_sum_ir - credit_sum_ir,
                            })
                    move_line_ir.append(adjust_credit_ir)
            
                elif debit_sum < credit_sum:
                    acc_id = journal_iva.default_debit_account_id.id
                    if not acc_id:
                        raise osv.except_osv(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Debit Account!')%(journal_iva.name))
                    adjust_debit = (0, 0, {
                                'name': _('Adjustment Entry'),
                                'date': ret.creation_date,
                                'partner_id': False,
                                'account_id': acc_id,
                                'journal_id': journal_iva.id,
                                'period_id': period,
                                'debit': credit_sum - debit_sum,
                                'credit': 0.0,
                            })
                    move_line_iva.append(adjust_debit)
                elif debit_sum_ir < credit_sum_ir:  
                    acc_id = journal_ir.default_debit_account_id.id
                    if not acc_id:
                        raise osv.except_osv(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Debit Account!')%(journal_ir.name))
                    adjust_debit = (0, 0, {
                                'name': _('Adjustment Entry'),
                                'date': ret.creation_date,
                                'partner_id': False,
                                'account_id': acc_id,
                                'journal_id': journal_ir.id,
                                'period_id': period,
                                'debit': credit_sum_ir - debit_sum_ir,
                                'credit': 0.0,
                            })
                    move_line_ir.append(adjust_debit)
                #import pdb
                #pdb.set_trace()     
                if renta == True:
                    acc_move_obj = self.pool.get('account.move')    
                    move_ir.update({'line_id': move_line_ir})
                    move_id_ir = acc_move_obj.create(cr, uid, move_ir, context=context)
                    self.write(cr, uid, [ret.id], {'move_id': move_id_ir, 'period_id' : period}, context=context)
                    if journal_ir.entry_posted: 
                        acc_move_obj.post(cr, uid, [move_id_ir], context=context) #omitir estado borrador
                elif iva == True:                           
                    acc_move_obj1= self.pool.get('account.move')            
                    move_iva.update({'line_id': move_line_iva})
                    move_id_iva = acc_move_obj1.create(cr, uid, move_iva, context=context)                        
                    self.write(cr, uid, [ret.id], {'move_id': move_id_iva, 'period_id' : period}, context=context)                
                    if journal_iva.entry_posted:
                        acc_move_obj1.post(cr, uid, [move_id_iva], context=context) #omitir estado borrador
            self.write(cr, uid, ids, {'state': 'approved'})
            return False
        
    
    
    def action_aprove(self,cr,uid,ids,context=None):            
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        journal_iva = company.journal_iva_id
        journal_ir = company.journal_ir_id       
        
        #OJO
        # HAY Q VALIDAR QUE SEA CORRECTO EL NUMERO DE RETENCION Y Q HAYA AUTORIZACION
        # PORQUE PUDO HABER MODIFICADO ESTOS CAMPOS
        
        #import pdb
        #pdb.set_trace()
        for ret in self.browse(cr,uid,ids,context=None):            
            #Para verificar que haya cuentas debe y haber en el diario, aunq no es necesario ya que
            #estas cuentas se sacaran desde la factura y los respectivos impuestos 
            if not journal_ir.default_debit_account_id:
                raise osv.except_osv('Error!', _("IR Retention Journal doesn't have debit account assigned!, can't complete operation"))
            if not journal_iva.default_debit_account_id:
                raise osv.except_osv('Error!', _("Iva Retention Journal doesn't have debit account assigned!, can't complete operation"))
            #lineas contables no conciliadas que pertenecen a la factura
            day = datetime.timedelta(days=5)
            add_date = datetime.datetime(*time.strptime(ret.invoice_id.date_invoice,'%Y-%m-%d')[:5])+ day            
            if ret.invoice_id.amount_total < ret.total:
                raise osv.except_osv('Error!', _("Amount of retention is bigger than residual value of invoice, please verify"))
            if ret.creation_date < ret.invoice_id.date_invoice:
                raise osv.except_osv('Error!', _("The date of retention can not be least than the date of invoice"))
            if ret.creation_date > add_date.strftime('%Y-%m-%d'):
                raise osv.except_osv('Error!', _("The date of retention can not be more than 5 days from the date of the invoice"))            
            if ((ret['transaction_type'])=='sale'):
                return self.crear_asiento_enventas(cr,uid,ids,ret,context)                
            elif(ret['transaction_type']=='purchase'):
                return self.crear_asiento_encompras(cr,uid,ids,ret,context)
        return True
    
    def action_cancel(self,cr,uid,ids,context=None):
        document_obj = self.pool.get('sri.type.document')
        retentions = self.pool.get('ecua.retencion').browse(cr, uid, ids, context)
        for ret in retentions:
            if ret.state == "draft":
                self.unlink(cr, uid, [ret.id,], context)
            else:
                if ret.transaction_type == "purchase":
                    for doc in ret.authorization_purchase_id.type_document_ids:
                        if doc.name=='withholding':
                            document_obj.rest_document(cr, uid, [doc.id,])
                    self.pool.get('ecua.retencion').write(cr, uid, [ret.id, ], {'state':'canceled'}, context)
                if ret.transaction_type == "sale":
                    vouchers = []
                    for vou in ret.account_voucher_ids:
                        vouchers.append(vou.id)
                    self.pool.get('account.voucher').cancel_voucher(cr, uid, vouchers, context)
                    self.pool.get('ecua.retencion').write(cr, uid, [ret.id, ], {'state':'canceled'}, context)
                    #self.pool.get('ecua.retencion').unlink(cr, uid, [ret.id, ], context)
        return True

        
    def button_aprove(self, cr, uid, ids, context=None):
        #import pdb
        #pdb.set_trace()
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            wf_service.trg_validate(uid, 'ecua.retencion', id, 'approve_signal', cr)
        return True
    
    def button_cancel(self, cr, uid, ids, context=None):
       
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            wf_service.trg_validate(uid, 'ecua.retencion', id, 'canceled_signal', cr)
        return True
    
    def action_draft(self, cr, uid, ids, context=None):
        
        self.write(cr, uid, ids, {'state':'draft'})
        return True    
    
    def button_set_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'draft'})
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            wf_service.trg_delete(uid, 'ecua.retencion', id, cr)
            wf_service.trg_create(uid, 'ecua.retencion', id, cr)
        return True    
    
    

ecua_retencion()

class ecua_retencion_line(osv.osv):
    
    """This have the lines of values retained"""
    def _amount_retained(self, cr, uid, ids, field_name, arg, context=None):        
        cur_obj = self.pool.get('res.currency')
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            value_retined = float(line.tax_base * (line.retention_percentage/100))
            cur = self.pool.get('res.users').browse(cr, uid, [uid,], context)[0]['company_id']['currency_id']
            res[line.id] = cur_obj.round(cr, uid, cur, value_retined)
        return res
    
    def _amount_retained_manual(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            value_retined = float(line.tax_base * (line.retention_percentage_manual/100))
            cur = self.pool.get('res.users').browse(cr, uid, [uid,], context)[0]['company_id']['currency_id']
            res[line.id] = cur_obj.round(cr, uid, cur, value_retined)
        return res

    def _percentaje_retained(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        porcentaje=tax=0.0        
        tax_obj = self.pool.get('account.tax')
        for line in self.browse(cr, uid, ids, context=context):
            tax_code_id = self.pool.get('account.tax.code').search(cr, uid, [('id', '=', line.tax_id.tax_code_id.id)])
            tax_code = None
            if tax_code_id:
                tax_code = self.pool.get('account.tax.code').browse(cr, uid, tax_code_id, context)[0]['code']            
            if (tax_code):
                tax = tax_obj.search(cr, uid, [('tax_code_id', '=', tax_code), ('child_ids','=',False)])
                porcentaje= (tax_obj.browse(cr, uid, tax, context)[0]['amount'])*(-100)
            res[line.id]= porcentaje
        return res
    

    def validar_description(self ,cr, id, ids, context=None):
        for ref in self.browse(cr,id,ids,context=None):
            if (ref['description']=='iva'):
                if ref['tax_id']['code']['type_ec']=='iva':
                    return True
                else:
                    return False
            elif (ref['description']=='renta'):
                if ref['tax_id']['code']['type_ec']=='renta':
                    return True
                else:
                    return False

    def _get_date(self, cr, uid, ids, field_names, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context):
            if line.retention_id:
                res[line.id] = line.retention_id.creation_date
            elif line.invoice_without_retention_id:
                res[line.id] = line.invoice_without_retention_id.date_invoice
        return res
    
    def _get_invoice(self, cr, uid, ids, field_names, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context):
            if line.invoice_retention_id:
                res[line.id] = line.invoice_retention_id.id
            elif line.invoice_without_retention_id:
                res[line.id] = line.invoice_without_retention_id.id
        return res
    
    _name= 'ecua.retencion.line'
    
    _columns = {
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year', required=True),
        'description': fields.selection([('iva', 'IVA'),('renta', 'RENTA'),('divisas', 'DIVISAS'),], 'Impuesto', required=True),
        'tax_id':fields.many2one('account.tax', 'Tax Code'), 
        'tax_base': fields.float('Tax Base', digits_compute=dp.get_precision('Account')),
        'retention_percentage_manual': fields.float('Percentaje Value', digits_compute=dp.get_precision('Account')), 
        'retained_value_manual': fields.function(_amount_retained_manual, method=True, type='float', string='Reatained Value',
                                          store={'ecua.retencion.line': (lambda self, cr, uid, ids, c={}: ids, ['tax_base','retention_percentage_manual'], 10)},), 
        'retention_percentage': fields.function(_percentaje_retained, method=True, type='float', string='Percentaje Value',
                                          store={'ecua.retencion.line': (lambda self, cr, uid, ids, c={}: ids, ['tax_id',], 1)},),
        'retained_value': fields.function(_amount_retained, method=True, type='float', string='Reatained Value',
                                          store={'ecua.retencion.line': (lambda self, cr, uid, ids, c={}: ids, ['tax_base','retention_percentage'], 10)},), 
        'sequence': fields.integer('Sequence'),
        'retention_id': fields.many2one('ecua.retencion', 'Retention', ondelete='cascade'),
        'creation_date_retention': fields.related('retention_id','creation_date', type='date', relation='ecua.retencion', string='Creation Date'), 
        'creation_date_invoice': fields.date('Creation Date'),
        'creation_date': fields.function(_get_date, method=True, store=True, string='Creation Date', type="date"), 
        'invoice_retention_id': fields.related('retention_id','invoice_id', type='many2one', relation='account.invoice', string='Invoice'), 
        'invoice_without_retention_id':fields.many2one('account.invoice', 'Document', required=False, ondelete="cascade"), 
        'invoice_id': fields.function(_get_invoice, method=True, store=True, string='Document', type="many2one", relation="account.invoice"), 
        'partner_id': fields.related('invoice_id', 'partner_id', type='many2one', relation='res.partner', string='Partner', store=True), 
        'period_id': fields.related('invoice_id', 'period_id', type='many2one', relation='account.period', string='Period', store=True), 
        'company_id': fields.related('invoice_id','company_id', type='many2one', relation='res.company', string='Company'),
        }
    
    _rec_name='sequence'
    
ecua_retencion_line()
