#########################################################################
# Copyright (C) 2013  ed.winTG, www.itx.ec                    	        #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################

{
    "name" : "Documentos complementarios Ecuador",
    "version" : "1.0",
    "author" : "SYSCOD Inc, syscod.comyr.com",
    "website" : "http://www.syscod.comyr.com/",
    "category" : "Regulación ecuatoriana",
    "depends" : ['base','ec_sri','ec_ruc'],
    "description": """
    Afecta a facturas, mediante el uso de documentos legales autorizados por el SRI:
    Retenciones:
                Entendemos como retención en la fuente, como una especie de mecanismo de cobro anticipado del 
                impuestos, mediante el cual la Administración Tributaria, ejecutada por el SRI,  obliga a 
                retener una parte de los impuestos causado por el contribuyente, con cargo a los ingresos que 
                perciba por ventas de bienes y prestación de servicios, según corresponda.
            Conceptos:
                RENTA.-
                IVA.-
                DIVISAS.-
    Notas de Crédito:
            Conceptos: 
                Errores de facturación: Se facturó un importe superior y luego se lo corrige con NC.
                Aplicación de bonificaciones y/o descuentos
                Devoluciones
                Casos de roturas de mercadería
    Notas de Débito:
            Conceptos:
                Error en la facturación.
                Intereses.
                Gastos por fletes.
                Gastos bancarios                
    """,
    "init_xml": [],
    "update_xml": [
     'views/ndc_view.xml',
     'views/ndd_view.xml',
     'views/retencion_view.xml',
     'views/invoice_view.xml', 
    ],
    "installable": True,
    "active": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
