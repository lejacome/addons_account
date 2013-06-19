 
from osv import osv, fields
import re
import decimal_precision as dp
from tools.translate import _
import time 

class res_company(osv.osv):
 
    _inherit = 'res.company'
 
    
    _columns = {
                'ruc':fields.char('RUC', size=13, required=False, readonly=False), 
                }
 
res_company()
 # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
