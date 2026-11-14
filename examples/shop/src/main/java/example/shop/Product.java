package example.shop;

public record Product(String id, String name, long priceCents, int stock) {
    public Product withStock(int newStock) {
        return new Product(id, name, priceCents, newStock);
    }
}
