package example.shop;

public record Order(long id, String productId, int quantity, long totalCents) {}
