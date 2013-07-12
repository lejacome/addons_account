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


class documentos_complementarios(osv.osv):
    _name="documentos.complementarios"
    _description = "Documentos Complementarios"

    _track = {
        'state': {
            'documentos_complementarios.mt_voucher_state_change': lambda self, cr, uid, obj, ctx=None: True,
        },
    }
    
    def _get_period(self, cr, uid, context=None):
        if context is None: context = {}
        if context.get('period_id', False):
            return context.get('period_id')
        periods = self.pool.get('account.period').find(cr, uid)
        return periods and periods[0] or False
    
    _columns = {
        'is_ndc':fields.boolean('Credit note'),
        'is_ndd':fields.boolean('Debit note'),
        'state':fields.selection(
                                 [('draft','Draft'),
                                  ('cancel','Cancelled'),
                                  ('proforma','Pro-forma'),
                                  ('posted','Posted')], 
                                 'Status', readonly=True, size=32, track_visibility='onchange',
                                 help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed Voucher. \
                                 \n* The \'Pro-forma\' when voucher is in Pro-forma status,voucher does not have an voucher number. \
                                 \n* The \'Posted\' status is used when user create voucher,a voucher number is generated and voucher entries are created in account \
                                 \n* The \'Cancelled\' status is used when user cancel voucher.'),
        #'is_retencion':fields.boolean('Retention'),
        # DEFINE EL TIPO de DOC
        'name':fields.char('Nombre',size=64),
        'ruc':fields.char('RUC o CI/Pass', size=13),
        'denominacion':fields.char('Denominacion', size=32),
        'doc_number':fields.char('Numero', size=17, readonly=True, help="Numero unico del documento rectificativo."),
        'num_atoriza':fields.char('Autorizacion', size=13,readonly=True),
        'autoriza_date_emision':fields.date('Fecha emision', readonly=True),
        'autoriza_date_expire':fields.date('Fecha caducidad', readonly=True),#Hay que calcular y verificar cuantos dias tiene de validez
        'nom_comercial':fields.char('Nombre Comercial',size=80),
        'razon_social':fields.char('Razon Social',size=80),
        'dir_matriz':fields.char('Direccion Matriz', size=80),
        'dir_sucursal':fields.char('Direccion Sucursal', size=80),
        'customer_name':fields.char('Cliente', size=80),
        'customer_ruc':fields.char('RUC/CI',size=13),
        'customer_dir':fields.char('Direccion', size=80),
        'fecha_emision':fields.date('Fecha de emision'),
        'tipo_comprob_venta':fields.selection([
                ('factura','Factura'),
                ('nota_venta','Nota de Venta')],'Tipo comprobante', select=True),
        'num_comprob_venta':fields.many2one('account.invoice','Numero',states={'approved':[('readonly',True)], 'canceled':[('readonly',True)]}, ondelete='cascade'),
        'lineas':fields.char('LINEAS', size=10),
        
        #'document_id': fields.many2one('account.invoice','Document'),
        'company_id':fields.many2one('res.company', 'Company'),
        #'journal_id': fields.many2one('account.journal', 'Journal', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'journal_id': fields.many2one('account.journal', 'Journal'),
        #'shop_id':fields.many2one('sale.shop', 'Shop', readonly=True, states={'draft':[('readonly',False)]}),
        'shop_id':fields.many2one('sale.shop', 'Shop', readonly=True, states={'draft':[('readonly',False)]}),
        
        'ejercicio_fiscal':fields.char('Ejercicio fiscal', size=12),
        #para las NdC, NdD y Retenciones
        'iva12':fields.integer('IVA12' ),
        'iva0':fields.integer('IVA0'),
        'valor_total':fields.float('Valor total'),
        'valor_retenido':fields.float('Valor retenido'),
        'audit': fields.related('move_id','to_check', type='boolean', help='Check this box if you are unsure of that journal entry and if you want to note it as \'to be reviewed\' by an accounting expert.', relation='account.move', string='To Review'), 
        'move_id':fields.many2one('account.move', 'Account Entry'),
        'move_ids': fields.related('move_id','line_id', type='one2many', relation='account.move.line', string='Journal Items', readonly=True),
        'period_id': fields.many2one('account.period', 'Period', readonly=True, states={'draft':[('readonly',False)]}),
        'partner_id':fields.many2one('res.partner', 'Partner', change_default=1, readonly=True, states={'draft':[('readonly',False)]}),   
    }

    _defaults = {
        'period_id': _get_period,
        'state': 'draft',
               }

        
documentos_complementarios()



