# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    next_picking_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Next Operation Responsible",
        compute="_compute_next_picking_user_id",
        store=True,
        help="Responsible of the first chained transfer that follows this one, "
        "e.g. who packs what this transfer picks.",
    )

    @api.depends("move_ids.move_dest_ids.picking_id.user_id")
    def _compute_next_picking_user_id(self):
        for picking in self:
            next_pickings = picking.move_ids.move_dest_ids.picking_id.filtered(
                lambda p: p.state not in ("done", "cancel")
            )
            picking.next_picking_user_id = next_pickings[:1].user_id

    def action_confirm(self):
        res = super().action_confirm()
        # Chained transfer confirmed after the previous one already got its
        # responsible (e.g. created by hand): assign it now.
        for picking in self.filtered(
            lambda p: p.picking_type_id.responsible_assign_mode == "previous"
        ):
            previous = picking.move_ids.move_orig_ids.picking_id.filtered(
                lambda p: p.user_id
                and p.picking_type_id.responsible_assign_mode != "manual"
                and p.user_id in p.picking_type_id._get_assignable_users()
            )
            previous[:1]._auto_assign_chained_responsible()
        return res

    def action_auto_assign_responsible(self):
        self._auto_assign_responsible(force=True)

    def _auto_assign_responsible(self, force=False):
        """Assign the least loaded user of the operation type pool.

        Without ``force`` a responsible already in the pool is kept, so a
        manual choice of the warehouse manager is respected and repeated
        reservations do not reshuffle the work. A responsible outside the
        pool (the salesperson that confirmed the order, the scheduler bot)
        is always replaced.
        """
        for picking in self:
            picking_type = picking.picking_type_id
            users = picking_type._get_assignable_users()
            if not users:
                continue
            if not force and picking.user_id in users:
                continue
            # sudo: the reservation may run as a salesperson or the scheduler,
            # which may not see or write every pending transfer.
            picking_sudo = picking.sudo()
            picking_sudo.user_id = picking_type.sudo()._get_least_loaded_user(users)
            picking_sudo._auto_assign_chained_responsible(force=force)

    def _auto_assign_chained_responsible(self, force=False):
        for picking in self:
            next_pickings = picking.move_ids.move_dest_ids.picking_id.filtered(
                lambda p: p.state not in ("done", "cancel")
                and p.picking_type_id.responsible_assign_mode == "previous"
            )
            for next_picking in next_pickings:
                if next_picking.picking_type_id.responsible_assign_same_user:
                    next_picking.user_id = picking.user_id
                    next_picking._auto_assign_chained_responsible(force=force)
                else:
                    next_picking._auto_assign_responsible(force=force)
