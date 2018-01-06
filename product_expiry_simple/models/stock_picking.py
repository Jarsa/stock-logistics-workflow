# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# © 2018 Jarsa Sistemas (Sarai Osorio <sarai.osorio@jarsa.com.mx>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api


class StockMoveLine(models.Model):
    _inherit = 'stock.picking'

