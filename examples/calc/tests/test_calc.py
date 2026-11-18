import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calc import can_checkout, shipping, subtotal  # noqa: E402


class CartTest(unittest.TestCase):
    def test_subtotal_adds_prices(self):
        self.assertEqual(subtotal([10, 2.5]), 12.5)

    def test_negative_price_is_refused(self):
        # Weak on purpose: no test with a price of 0, so `<` -> `<=` survives.
        with self.assertRaises(ValueError):
            subtotal([-1])

    def test_shipping(self):
        # Weak on purpose: nothing checks exactly 50, so `>=` -> `>` survives.
        self.assertEqual(shipping(80), 0)
        self.assertEqual(shipping(10), 5)

    def test_checkout(self):
        self.assertTrue(can_checkout(1, True))
        self.assertFalse(can_checkout(0, True))


if __name__ == "__main__":
    unittest.main()
