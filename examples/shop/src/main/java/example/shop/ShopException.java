package example.shop;

import org.springframework.http.HttpStatus;

/** A business rule was broken; carries the HTTP status the API returns. */
public class ShopException extends RuntimeException {
    private final HttpStatus status;

    public ShopException(HttpStatus status, String message) {
        super(message);
        this.status = status;
    }

    public HttpStatus status() {
        return status;
    }
}
