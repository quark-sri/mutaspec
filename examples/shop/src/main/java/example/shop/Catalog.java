package example.shop;

import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;

/** In-memory product catalogue with stock (R1, R3, R4). */
@Component
public class Catalog {
    private final Map<String, Product> products = new ConcurrentHashMap<>();

    public Catalog() {
        add(new Product("pen", "Pen", 250, 100));
        add(new Product("book", "Book", 2500, 20));
        add(new Product("lamp", "Lamp", 4000, 5));
        add(new Product("chair", "Chair", 12000, 3));
    }

    public void add(Product product) {
        products.put(product.id(), product);
    }

    public Optional<Product> find(String id) {
        return Optional.ofNullable(products.get(id));
    }

    /** Takes `quantity` out of stock, or fails without changing anything. */
    public synchronized Product take(String id, int quantity) {
        Product product = find(id).orElseThrow(() -> Errors.unknownProduct(id));
        if (product.stock() < quantity) {
            throw new ShopException(
                    HttpStatus.CONFLICT,
                    "only " + product.stock() + " of " + id + " in stock");
        }
        Product updated = product.withStock(product.stock() - quantity);
        products.put(id, updated);
        return updated;
    }
}
