package example.shop;

import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

/** Places and reads orders (R2-R7). */
@Service
public class OrderService {
    static final int MIN_QUANTITY = 1;
    static final int MAX_QUANTITY = 10;

    private final Catalog catalog;
    private final Pricing pricing;
    private final Map<Long, Order> orders = new ConcurrentHashMap<>();
    private final AtomicLong nextId = new AtomicLong(1);

    public OrderService(Catalog catalog, Pricing pricing) {
        this.catalog = catalog;
        this.pricing = pricing;
    }

    public Order place(OrderRequest request) {
        if (request.quantity() < MIN_QUANTITY || request.quantity() > MAX_QUANTITY) {
            throw new ShopException(
                    HttpStatus.BAD_REQUEST,
                    "quantity must be from " + MIN_QUANTITY + " to " + MAX_QUANTITY);
        }
        Product product = catalog.take(request.productId(), request.quantity());
        long total = pricing.total(product.priceCents(), request.quantity());
        Order order = new Order(nextId.getAndIncrement(), product.id(), request.quantity(), total);
        orders.put(order.id(), order);
        return order;
    }

    public Optional<Order> find(long id) {
        return Optional.ofNullable(orders.get(id));
    }
}
