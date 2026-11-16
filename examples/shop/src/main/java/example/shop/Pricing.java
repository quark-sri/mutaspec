package example.shop;

import org.springframework.stereotype.Component;

/** Order totals and the bulk discount (R5, R6). */
@Component
public class Pricing {
    static final long DISCOUNT_FROM_CENTS = 10_000;
    static final int DISCOUNT_PERCENT = 10;

    public long total(long unitPriceCents, int quantity) {
        long subtotal = unitPriceCents * quantity;
        if (subtotal >= DISCOUNT_FROM_CENTS) {
            return subtotal - subtotal * DISCOUNT_PERCENT / 100;
        }
        return subtotal;
    }
}
