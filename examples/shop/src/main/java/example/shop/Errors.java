package example.shop;

import org.springframework.http.HttpStatus;

final class Errors {
    private Errors() {}

    static ShopException unknownProduct(String id) {
        return new ShopException(HttpStatus.NOT_FOUND, "unknown product " + id);
    }
}
