# -*- coding: utf-8 -*-
# Copyright 2017 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    @api.multi
    def process_assign_ordered_qty(self):
        """Autocomplete product qty with producto ordered qty only for
        products without lots track"""
        self.ensure_one()
        for move_line in self.pick_ids.move_line_ids:
            if move_line.product_id.tracking == 'lot':
                continue
            move_line.qty_done = move_line.product_uom_qty
        self._process()
