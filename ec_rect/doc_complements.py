# -*- coding: utf-8 -*-
#############################################################################
#     OpenERP, Open Source Management Solution                              #
#     Copyright (C) 2013  ed.winTG, www.itx.ec                              #
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
        'is_retencion':fields.boolean('Retention'),
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
        'num_comprob_venta':fields.many2one('account.invoice','Numero', required=True),
        'lineas':fields.char('LINEAS', size=10),
        
        #'document_id': fields.many2one('account.invoice','Document'),
        'company_id':fields.many2one('res.company', 'Company'),
        #'journal_id': fields.many2one('account.journal', 'Journal', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'journal_id': fields.many2one('account.journal', 'Journal', required=True),
        #'shop_id':fields.many2one('sale.shop', 'Shop', readonly=True, states={'draft':[('readonly',False)]}),
        'shop_id':fields.many2one('sale.shop', 'Shop'),
        'ejercicio_fiscal':fields.char('Ejercicio fiscal', size=12, required=True),
        #para las NdC, NdD y Retenciones
        'iva12':fields.integer('IVA12' ),
        'iva0':fields.integer('IVA0'),
        'valor_total':fields.float('Valor total'),
        'valor_retenido':fields.float('Valor retenido'), 
        'state': fields.selection([
                ('draft','Draft'),
                ('proforma','Pro-forma'),
                ('proforma2','Pro-forma'),
                ('open','Open'),
                ('paid','Paid'),
                ('wait_invoice','Waiting Invoice'),
                ('cancel','Cancelled')
                ],'State', select=True, readonly=True,
                help=' * The \'Draft\' state is used when a user is encoding a new and unconfirmed Invoice. \
                \n* The \'Pro-forma\' when invoice is in Pro-forma state,invoice does not have an invoice number. \
                \n* The \'Open\' state is used when user create invoice,a invoice number is generated.Its in open state till user does not pay invoice. \
                \n* The \'Paid\' state is set automatically when invoice is paid.\
                \n* The \'Cancelled\' state is used when user cancel invoice.'),                   
    }

        
documentos_complementarios()

class ecua_ndc(osv.osv):
    _name = 'ecua.ndc'
    _inherits={'documentos.complementarios':'document_id'}
    _description='Credit Notes'
    
    def check_ref(self, cr, uid, ids):
        partner_obj = self.pool.get('res.partner')
        for data in self.browse(cr, uid, ids):
            return partner_obj.check_ced(data.ruc).get('valid', False)
    
    def _default_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id and user.company_id.id or False
    
    _columns = {
                 'document_id': fields.many2one('documentos.complementarios','Document',ondelete='cascade'),
                 'ndc_line_ids':fields.one2many('ecua.ndc_line','ecua_ndc_id','Lineas N. Credito'),             
                 'ndc_concept':fields.selection([
                ('error','Error de Facturacion'),
                ('bono','Aplica bono y/o descuento'),
                ('devolucion','Devoluciones'),
                ('mercaderia','Rotura de mercaderia')],'Concepto', select=True),		 
             }
    _defaults = {'denominacion': 'Credit Note',
                 'is_ndc': lambda *a: 1,  
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
        return {'value': values} or False

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
                next_number = doc_obj.get_next_value_secuence(cr, uid, name_document, False, printer_id, 'ecua.ndc', name_field, context)
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
            address=address +" & "+curr_user.company_id.street2 
        if(curr_user.company_id.city):
            address=address+" - "+curr_user.company_id.city+"."   
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
                auth_line_id = doc_obj.search(cr, uid, [('name','=','credit_note'), ('printer_id','=',printer.id), ('state','=',True)])
                if auth_line_id:
                    auth_line = doc_obj.browse(cr, uid, auth_line_id[0],context)
                    values['num_atoriza'] = auth_line.sri_authorization_id.number
                    values['autoriza_date_emision'] = auth_line.sri_authorization_id.start_date
                    values['autoriza_date_expire'] = auth_line.sri_authorization_id.expiration_date
                    values['doc_number'] = doc_obj.get_next_value_secuence(cr, uid, 'credit_note', False, printer.id, 'ecua.ndc', 'doc_number', context)
                    values['fecha_emision'] = time.strftime('%Y-%m-%d')
                    values['denominacion']='Nota de credito'
        return values
            
ecua_ndc()


class ecua_ndc_line(osv.osv):
    _name = 'ecua.ndc_line' 
    _description = 'Lineas de la Nota de credito'
    _columns = {
                'name':fields.char('Nombre', size=64, readonly=False),
                'ecua_ndc_id':fields.many2one('ecua.ndc','Nota'),
                'motivo_modifica':fields.char('Motivo', size=64,required=True),
                'valor_modifica':fields.float('Valor a modificar', required=True),  
                }
    
    def onchange_impuestos_ids(self, cr, uid, ids, comprobante_id, context=None):
        return True
    def calcula_ndc(self, cr, uid, ids, comprobante_id, context=None):
        return True
    
ecua_ndc_line()


class ecua_ndd(osv.osv):
    _name = 'ecua.ndd'
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
ecua_ndd()

class ecua_ndd_line(osv.osv):
    _name = 'ecua.ndd_line' 
    _description = 'Lineas de la Nota de debito'
    _columns = {
                'name':fields.char('Nombre', size=64, readonly=False),
                'ecua_ndd_id':fields.many2one('ecua.ndd','Nota'),
                'motivo_modifica':fields.char('Motivo', size=64,required=True),
                'valor_modifica':fields.float('Valor a modificar', required=True),
                'iva12':fields.integer('IVA', readonly=True),
                'iva0':fields.integer('IVA', readonly=True),
                'valor_total':fields.float('Valor total'),                
                }
    
    def onchange_impuestos_ids(self, cr, uid, ids, comprobante_id, context=None):
        return True
    def calcula_ndd(self, cr, uid, ids, comprobante_id, context=None):
        return True
    
ecua_ndd_line()

class ecua_retencion(osv.osv):
    _name = 'ecua.retencion'
    _inherits={'documentos.complementarios':'document_id'}
    _description='Retention'
    
    def check_ref(self, cr, uid, ids):
        partner_obj = self.pool.get('res.partner')
        for data in self.browse(cr, uid, ids):
            return partner_obj.check_ced(data.ruc).get('valid', False)
    
    def _default_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id and user.company_id.id or False
    
    _columns = {                 
                 'document_id': fields.many2one('documentos.complementarios','Document',ondelete='cascade'),
                 'retencion_line_ids':fields.one2many('ecua.retencion_line','ecua_retencion_id','Lineas de la retencion'),
                 'retencion_concept':fields.selection([
                ('error','Error de Facturacion'),
                ('interes','Intereses'),
                ('flete','Gastos por fletes'),
                ('banco','Gastos bancarios')],'Concepto', select=True),           
             
             }

    _defaults = {'company_id':_default_company,
                 'is_retencion': lambda *a: 1, 
               }
    def onChange_comprobante(self, cr, uid, ids, comprobante_id, context=None):
        values={}
        comprobant=self.pool.get('account.invoice').browse(cr, uid,comprobante_id, context)
        values['customer_name']=comprobant.partner_id.name
        values['customer_ruc']=comprobant.partner_id.ref
        #import pdb
        #pdb.set_trace()
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
                next_number = doc_obj.get_next_value_secuence(cr, uid, name_document, False, printer_id, 'ecua.retencion', name_field, context)
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
                auth_line_id = doc_obj.search(cr, uid, [('name','=','withholding'), ('printer_id','=',printer.id), ('state','=',True)])
                if auth_line_id:
                    auth_line = doc_obj.browse(cr, uid, auth_line_id[0],context)
                    values['num_atoriza'] = auth_line.sri_authorization_id.number
                    values['autoriza_date_emision'] = auth_line.sri_authorization_id.start_date
                    values['autoriza_date_expire'] = auth_line.sri_authorization_id.expiration_date
                    values['doc_number'] = doc_obj.get_next_value_secuence(cr, uid, 'withholding', False, printer.id, 'ecua.retencion', 'doc_number', context)
                    values['fecha_emision'] = time.strftime('%Y-%m-%d')
                    values['denominacion']='Comprobante de Retencion'
                    
        return values
ecua_retencion()

class ecua_retencion_line(osv.osv):
    _name = 'ecua.retencion_line' 
    _description = 'Lineas de la retencion'
    _columns = {
                'name':fields.char('Nombre', size=64, readonly=False),
                'ecua_retencion_id':fields.many2one('ecua.retencion','Retencion'),
                'ejercicio_fiscal':fields.char('Ejercicio fiscal', size=12,required=True),
                'base_imponible':fields.float('Base imponible para la retencion', required=True),
                'impuesto_id':fields.many2one('account.tax','Impuesto'),
                'porcentaje':fields.char('% de Retencion ', size=12),               
                }
    
    def onchange_impuestos_ids(self, cr, uid, ids, comprobante_id, context=None):
        return True
    def calcula_retencion(self, cr, uid, ids, comprobante_id, context=None):
        return True
    
ecua_retencion_line()
