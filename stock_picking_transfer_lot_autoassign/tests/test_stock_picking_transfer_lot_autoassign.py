# -*- coding: utf-8 -*-
# Copyright 2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestStockPickingTransferLotAutoAssign(common.TransactionCase):
    def setUp(self):
        super(TestStockPickingTransferLotAutoAssign, self).setUp()
        self.partner = self.env['res.partner'].search([], limit=1)
        self.warehouse = self.env['stock.warehouse'].search([], limit=1)
        self.picking_type = self.env['stock.picking.type'].search([
            ('warehouse_id', '=', self.warehouse.id),
            ('code', '=', 'outgoing'),
        ], limit=1)
        self.picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.picking_type.id,
            'location_id': self.picking_type.default_location_src_id.id,
            'location_dest_id': self.partner.property_stock_customer.id,
        })
        self.product = self.env['product.product'].search([
            ('type', '=', 'product'), ('tracking', '=', 'lot')], limit=1)
        self.product_no_lot = self.env['product.product'].search([
            ('type', '=', 'product'), ('tracking', '=', 'none')], limit=1)
        self.lot1 = self.env['stock.production.lot'].create({
            'product_id': self.product.id,
            'name': 'Lot 1',
        })
        self.quant1 = self.env['stock.quant'].create({
            'product_id': self.product.id,
            'location_id': self.picking.location_id.id,
            'quantity': 6,
            'lot_id': self.lot1.id,
        })
        self.lot2 = self.env['stock.production.lot'].create({
            'product_id': self.product.id,
            'name': 'Lot 2',
        })
        self.quant2 = self.env['stock.quant'].create({
            'product_id': self.product.id,
            'location_id': self.picking.location_id.id,
            'quantity': 10,
            'lot_id': self.lot2.id,
        })
        self.quant_no_lot = self.env['stock.quant'].create({
            'product_id': self.product_no_lot.id,
            'location_id': self.picking.location_id.id,
            'quantity': 10,
        })
        self.Move = self.env['stock.move']
        self.move = self.Move.create({
            'name': 'TEST/MOVE',
            'product_uom': self.product.uom_id.id,
            'location_id': self.picking_type.default_location_src_id.id,
            'location_dest_id': self.partner.property_stock_customer.id,
            'picking_id': self.picking.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'partner_id': self.picking.partner_id.id,
            })

    def test_transfer(self):
        self.picking.action_confirm()
        self.picking.action_assign()
        pack_ops = self.picking.move_line_ids
        self.assertEqual(len(pack_ops), 1)
        counter = 0
        for ml in pack_ops:
            if ml.product_id.tracking == 'lot':
                counter += 1
        self.assertEqual(counter, 1)
        self.assertEqual(pack_ops.qty_done, 1)

    def test_autocomplete_backorder(self):
        """Adds move with a product with 'none' lot track"""
        self.Move = self.env['stock.move']
        self.move = self.Move.create({
            'name': 'TEST/MOVE2',
            'product_uom': self.product_no_lot.uom_id.id,
            'location_id': self.picking_type.default_location_src_id.id,
            'location_dest_id': self.partner.property_stock_customer.id,
            'picking_id': self.picking.id,
            'product_id': self.product_no_lot.id,
            'product_uom_qty': 10,
            'partner_id': self.picking.partner_id.id,
            })
        self.picking.action_confirm()
        self.picking.action_assign()
        backorder_wiz = self.env['stock.backorder.confirmation'].create({
            'pick_ids': [(6, 0, self.picking.ids)],
            })
        backorder_wiz.process_assign_ordered_qty()
        pack_ops = self.picking.move_line_ids
        self.assertEqual(len(pack_ops), 2)
        self.assertEqual(pack_ops[1].qty_done, 10)
