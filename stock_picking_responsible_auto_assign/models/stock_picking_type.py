# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models

PENDING_STATES = ("confirmed", "waiting", "assigned")


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    responsible_user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="stock_picking_type_responsible_user_rel",
        string="Responsible Pool",
        domain=lambda self: [
            ("all_group_ids", "in", self.env.ref("stock.group_stock_user").id)
        ],
        help="Users that receive the transfers of this operation type "
        "automatically. The transfer goes to the user with the lowest "
        "pending workload.",
    )
    responsible_assign_mode = fields.Selection(
        selection=[
            ("manual", "Manual"),
            ("ready", "When the transfer is ready"),
            ("previous", "Together with the previous operation"),
        ],
        string="Responsible Assignment",
        default="manual",
        required=True,
        help="Manual: nothing is assigned automatically.\n"
        "When the transfer is ready: assign the responsible as soon as the "
        "transfer is reserved.\n"
        "Together with the previous operation: assign the responsible when "
        "the chained previous transfer (e.g. pick before pack) gets its own "
        "responsible, so both users are known from the start.",
    )
    responsible_assign_same_user = fields.Boolean(
        string="Same Responsible as Previous Operation",
        help="Copy the responsible of the previous transfer instead of "
        "balancing the workload within the pool of this operation type.",
    )
    responsible_assign_load = fields.Selection(
        selection=[
            ("moves", "Number of lines"),
            ("quantity", "Quantity"),
            ("pickings", "Number of transfers"),
        ],
        string="Workload Measure",
        default="moves",
        required=True,
        help="What is summed over the pending transfers of each user to pick "
        "the least loaded one.",
    )

    def _get_assignable_users(self):
        self.ensure_one()
        return self.responsible_user_ids.filtered(
            lambda u: u.active and u.picking_assign_available
        )

    def _get_picking_load(self, picking):
        if self.responsible_assign_load == "quantity":
            return sum(picking.move_ids.mapped("product_uom_qty"))
        if self.responsible_assign_load == "pickings":
            return 1
        return len(picking.move_ids)

    def _get_least_loaded_user(self, users):
        """Return the user of ``users`` with the lowest pending workload on
        this operation type. Ties are broken by the number of pending
        transfers and then by user id."""
        self.ensure_one()
        load = dict.fromkeys(users, 0.0)
        count = dict.fromkeys(users, 0)
        pending = self.env["stock.picking"].search(
            [
                ("picking_type_id", "=", self.id),
                ("user_id", "in", users.ids),
                ("state", "in", PENDING_STATES),
            ]
        )
        for picking in pending:
            load[picking.user_id] += self._get_picking_load(picking)
            count[picking.user_id] += 1
        return min(users, key=lambda u: (load[u], count[u], u.id))
