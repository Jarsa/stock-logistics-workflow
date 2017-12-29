# Copyright 2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        self.ensure_one()
        """Auto-assign as done the quantity proposed for the lots"""
        res = super(StockMove, self)._prepare_move_line_vals(
            quantity, reserved_quant)
        if self.picking_type_id.avoid_internal_assignment:
            return
        if self.product_id.tracking == 'lot':
            res['qty_done'] = quantity
        return res
