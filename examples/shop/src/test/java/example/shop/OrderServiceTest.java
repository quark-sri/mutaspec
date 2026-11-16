package example.shop;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;

class OrderServiceTest {
    private final Catalog catalog = new Catalog();
    private final OrderService service = new OrderService(catalog, new Pricing());

    @Test
    void placingAnOrderTakesStock() {
        Order order = service.place(new OrderRequest("book", 2));

        assertEquals(5000, order.totalCents());
        assertEquals(18, catalog.find("book").orElseThrow().stock());
    }

    @Test
    void zeroQuantityIsRejected() {
        ShopException error =
                assertThrows(ShopException.class, () -> service.place(new OrderRequest("pen", 0)));

        assertEquals(HttpStatus.BAD_REQUEST, error.status());
    }

    @Test
    void ordersCanBeReadBack() {
        Order order = service.place(new OrderRequest("pen", 1));

        assertEquals(order, service.find(order.id()).orElseThrow());
    }
}
