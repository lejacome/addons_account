##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2010-2011 STRACONX S.A. (<http://openerp.straconx.com>). All Rights Reserved
#    
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
  "name" : "Ciudades, Provincias y Regiones de Ecuador",
  "version" : "0.1",
  "author" : "SYSCOD Inc, syscod.comyr.com",
  "website" : "http://www.syscod.comyr.com/",
  "category" : "Regulación ecuatoriana",
  "description" : """Permite ingresar las provincias y ciudades de Ecuador en el objeto res.country.state, 
  res.region.state y city.city""",
  "depends" : ['base'],
  "update_xml" : [
                'views/partner_view.xml',
                'views/states_view.xml',
                'views/menu.xml',
                'data/ecuadorian_states.xml',
                'security/ir.model.access.csv'
                ],
  "installable" : True,
  "active" : False,
}

