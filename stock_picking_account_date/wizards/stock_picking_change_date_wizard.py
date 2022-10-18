# Copyright 2021, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, fields, models
from odoo.exceptions import UserError


class StockPickingChangeDateWizard(models.TransientModel):
    _name = 'stock.picking.change.date.wizard'
    _description = ('Wizard to allow to change date to picking and related'
                    ' account move.')

    date = fields.Datetime(required=True)

    def change_date(self):
        self.ensure_one()
        if self.date.date() > fields.Date.context_today(self):
            raise UserError(_('You cannot define a date in the future.'))
        pickings = self.env['stock.picking'].browse(
            self._context.get('active_ids'))
        states = all(state == 'done' for state in pickings.mapped('state'))
        if not states:
            raise UserError(_("All the pickings must be in state 'Done'"))
        scraps = self.env['stock.scrap'].search([
            ('picking_id', 'in', pickings.ids),
        ])
        moves = (pickings.mapped('move_lines') + scraps.mapped('move_id'))
        svls = moves.mapped('stock_valuation_layer_ids')
        account_moves = svls.mapped('account_move_id')
        date_tz = fields.Datetime.context_timestamp(self, self.date)
        date_str = fields.Datetime.to_string(date_tz)
        pickings.write({
            'accounting_date': date_str,
            'date_done': self.date,
        })
        moves.write({
            'date': date_str,
        })
        moves.mapped('move_line_ids').write({
            'date': date_str,
        })
        # Use of SQL as Odoo don't allow to change create_date field.
        self.env.cr.execute('''
            UPDATE stock_valuation_layer
            SET create_date = %s
            WHERE id IN %s
            ''', (
            fields.Datetime.to_string(self.date),
            tuple(svls.ids)))
        account_moves.button_draft()
        account_moves.write({
            'name': '/',
            'date': date_str,
        })
        for account_move in account_moves:
            account_move.action_post()
