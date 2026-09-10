# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    # `location_ids` did not depend on the quant quantity, so lots whose
    # quants only changed in quantity kept a stale value. The dependency is
    # fixed now, but the already stored values still need a recompute.
    env = api.Environment(cr, SUPERUSER_ID, {})
    lot_model = env["stock.lot"]
    env.add_to_compute(lot_model._fields["location_ids"], lot_model.search([]))
    env.flush_all()
