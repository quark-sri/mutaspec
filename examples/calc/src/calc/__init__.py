"""A tiny shopping cart: the code that mutaspec plants bugs in."""

FREE_SHIPPING_FROM = 50
SHIPPING = 5


def subtotal(prices: list[float]) -> float:
    total = 0.0
    for price in prices:
        if price < 0:
            raise ValueError("price must not be negative")
        total = total + price
    return total


def shipping(subtotal: float) -> float:
    if subtotal >= FREE_SHIPPING_FROM:
        return 0
    return SHIPPING


def can_checkout(items: int, logged_in: bool) -> bool:
    return items > 0 and logged_in
