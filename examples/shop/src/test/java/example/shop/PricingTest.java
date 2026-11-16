package example.shop;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class PricingTest {
    private final Pricing pricing = new Pricing();

    @Test
    void totalIsPriceTimesQuantity() {
        assertEquals(750, pricing.total(250, 3));
    }

    @Test
    void largeOrdersGetTenPercentOff() {
        assertEquals(21_600, pricing.total(12_000, 2));
    }
}
