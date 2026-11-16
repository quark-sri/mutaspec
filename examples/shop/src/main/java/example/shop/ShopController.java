package example.shop;

import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ShopController {
    private final Catalog catalog;
    private final OrderService orders;

    public ShopController(Catalog catalog, OrderService orders) {
        this.catalog = catalog;
        this.orders = orders;
    }

    @GetMapping("/products/{id}")
    public Product product(@PathVariable String id) {
        return catalog.find(id).orElseThrow(() -> Errors.unknownProduct(id));
    }

    @PostMapping("/orders")
    public ResponseEntity<Order> place(@RequestBody OrderRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED).body(orders.place(request));
    }

    @GetMapping("/orders/{id}")
    public Order order(@PathVariable long id) {
        return orders.find(id)
                .orElseThrow(() -> new ShopException(HttpStatus.NOT_FOUND, "unknown order " + id));
    }

    @ExceptionHandler(ShopException.class)
    public ResponseEntity<Map<String, String>> handle(ShopException error) {
        return ResponseEntity.status(error.status()).body(Map.of("error", error.getMessage()));
    }
}
