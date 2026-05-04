# Copyright 2020 Alan Ramos - Jarsa
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.tests.common import TransactionCase


class TestStockPickingFilterProduct(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.other_location = cls.env["stock.location"].create(
            {
                "name": "Other Internal Location",
                "usage": "internal",
                "location_id": cls.env.ref("stock.stock_location_locations").id,
            }
        )
        cls.product_non_storable = cls.env["product.product"].create(
            {
                "name": "Test Non Storable",
                "type": "consu",
                "is_storable": False,
            }
        )
        cls.product_with_stock = cls.env["product.product"].create(
            {
                "name": "Test With Stock",
                "type": "consu",
                "is_storable": True,
            }
        )
        cls.product_without_stock = cls.env["product.product"].create(
            {
                "name": "Test Without Stock",
                "type": "consu",
                "is_storable": True,
            }
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product_with_stock, cls.stock_location, 10.0
        )
        cls.env.flush_all()

    def _search_with_filter(self, location):
        domain = [
            "|",
            ("is_storable", "=", False),
            ("location_ids", "child_of", location.id),
        ]
        return self.env["product.product"].search(domain)

    def test_location_ids_empty_without_stock(self):
        self.assertFalse(self.product_without_stock.location_ids)

    def test_location_ids_contains_location_with_stock(self):
        self.assertIn(self.stock_location, self.product_with_stock.location_ids)

    def test_location_ids_does_not_contain_other_location(self):
        self.assertNotIn(self.other_location, self.product_with_stock.location_ids)

    def test_location_ids_updates_when_quant_added(self):
        product = self.env["product.product"].create(
            {"name": "Test Dynamic Stock", "type": "consu", "is_storable": True}
        )
        self.assertFalse(product.location_ids)
        self.env["stock.quant"]._update_available_quantity(
            product, self.other_location, 5.0
        )
        self.env.flush_all()
        self.assertIn(self.other_location, product.location_ids)

    def test_filter_shows_non_storable_product(self):
        products = self._search_with_filter(self.stock_location)
        self.assertIn(self.product_non_storable, products)

    def test_filter_shows_non_storable_product_even_without_local_stock(self):
        products = self._search_with_filter(self.other_location)
        self.assertIn(self.product_non_storable, products)

    def test_filter_shows_storable_product_with_stock_in_location(self):
        products = self._search_with_filter(self.stock_location)
        self.assertIn(self.product_with_stock, products)

    def test_filter_hides_storable_product_without_stock(self):
        products = self._search_with_filter(self.stock_location)
        self.assertNotIn(self.product_without_stock, products)

    def test_filter_hides_storable_product_in_different_location(self):
        products = self._search_with_filter(self.other_location)
        self.assertNotIn(self.product_with_stock, products)

    def test_filter_shows_storable_product_in_child_location(self):
        child_location = self.env["stock.location"].create(
            {
                "name": "Child of Stock",
                "usage": "internal",
                "location_id": self.stock_location.id,
            }
        )
        product = self.env["product.product"].create(
            {"name": "Test Child Location", "type": "consu", "is_storable": True}
        )
        self.env["stock.quant"]._update_available_quantity(product, child_location, 3.0)
        self.env.flush_all()
        # searching with the parent location must also find the product
        products = self._search_with_filter(self.stock_location)
        self.assertIn(product, products)
