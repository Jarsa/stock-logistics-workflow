# Copyright 2021, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Stock Picking Change Date',
    'summary': '''
        Wizard to allow to change date to picking and related account move.''',
    'version': '14.0.1.0.1',
    'category': 'Stock',
    'author': 'Jarsa Sistemas',
    'website': 'https://www.jarsa.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'stock_account',
    ],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'wizards/stock_picking_change_date_wizard_view.xml',
    ],
}
