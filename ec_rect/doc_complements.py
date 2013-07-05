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
    _columns = {
        'is_ndc':fields.boolean('Credit note'),
        'is_ndd':fields.boolean('Debit note'),
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
        'customer_name':fields.char('Cliente', size=80, required=True),
        'customer_ruc':fields.char('RUC/CI',size=13),
        'customer_dir':fields.char('Direccion', size=80),
        'fecha_emision':fields.date('Fecha de emision'),
        'tipo_comprob_venta':fields.selection([
                ('factura','Factura'),
                ('nota_venta','Nota de Venta')],'Tipo comprobante', select=True),
        'num_comprob_venta':fields.many2one('account.invoice','Numero', required=True,states={'approved':[('readonly',True)], 'canceled':[('readonly',True)]}, ondelete='cascade'),
        'lineas':fields.char('LINEAS', size=10),
        
        #'document_id': fields.many2one('account.invoice','Document'),
        'company_id':fields.many2one('res.company', 'Company'),
        #'journal_id': fields.many2one('account.journal', 'Journal', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'journal_id': fields.many2one('account.journal', 'Journal', required=True),
        #'shop_id':fields.many2one('sale.shop', 'Shop', readonly=True, states={'draft':[('readonly',False)]}),
        'shop_id':fields.many2one('sale.shop', 'Shop', readonly=True, states={'draft':[('readonly',False)]}),
        
        'ejercicio_fiscal':fields.char('Ejercicio fiscal', size=12, required=True),
        #para las NdC, NdD y Retenciones
        'iva12':fields.integer('IVA12' ),
        'iva0':fields.integer('IVA0'),
        'valor_total':fields.float('Valor total'),
        'valor_retenido':fields.float('Valor retenido'),    
    }


        
documentos_complementarios()



