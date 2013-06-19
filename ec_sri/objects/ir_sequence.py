# -*- coding: UTF-8 -*- #
#########################################################################
# Copyright (C) 2011  Christopher Ormaza, Ecuadorenlinea.net            #
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

from osv import osv, fields
import time
from tools.translate import _

class ir_sequence(osv.osv):
    _inherit = 'ir.sequence'
    
    def get_next_id(self, cr, uid, seq_ids, aditional_value=0, context=None):
        if not seq_ids:
            return False
        if context is None:
            context = {}
        if type(seq_ids) in (type(1), type(long)):
            seq_ids = [seq_ids]
        seq = self.read(cr, uid, seq_ids, ['company_id','implementation','number_next','prefix','suffix','padding'])[0]
        seq['number_next'] = seq['number_next'] + aditional_value
        d = self._interpolation_dict()
        #import pdb
        #pdb.set_trace()
        interpolated_prefix = self._interpolate(seq['prefix'], d)
        interpolated_suffix = self._interpolate(seq['suffix'], d)    
        return interpolated_prefix + '%%0%sd' % seq['padding'] % seq['number_next'] + interpolated_suffix

    def get_next_id1(self, cr, uid, seq_ids, aditional_value=0, context=None):
        if not seq_ids:
            return False
        if context is None:
            context = {}
        force_company = context.get('force_company')
        if not force_company:
            force_company = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
        sequences = self.read(cr, uid, seq_ids, ['company_id','implementation','number_next','prefix','suffix','padding'])
        preferred_sequences = [s for s in sequences if s['company_id'] and s['company_id'][0] == force_company ]
        seq = preferred_sequences[0] if preferred_sequences else sequences[0]
        cr.execute("SELECT number_next from ir_sequence where id=%s", (seq['id'],))
        seq['number_next'] = int(cr.fetchone()[0]) + aditional_value
        d = self._interpolation_dict()
        interpolated_prefix = self._interpolate(seq['prefix'], d)
        interpolated_suffix = self._interpolate(seq['suffix'], d)
        return interpolated_prefix + '%%0%sd' % seq['padding'] % seq['number_next'] + interpolated_suffix
    
    def get_next_id2(self, cr, uid, sequence_id, aditional_value=0, test='id', context=None):
        assert test in ('code','id')
        company_ids = self.pool.get('res.company').search(cr, uid, [], context=context)
        cr.execute('''SELECT id, number_next, prefix, suffix, padding
                      FROM ir_sequence
                      WHERE %s=%%s
                       AND active=true
                       AND (company_id in %%s or company_id is NULL)
                      ORDER BY company_id, id
                      FOR UPDATE NOWAIT''' % test,
                      (sequence_id, tuple(company_ids)))
        res = cr.dictfetchone()
        if res:
            if res['number_next']:
                return self._process(res['prefix']) + '%%0%sd' % res['padding'] % (res['number_next']+aditional_value) + self._process(res['suffix'])
            else:
                return self._process(res['prefix']) + self._process(res['suffix'])
        return False
ir_sequence()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: