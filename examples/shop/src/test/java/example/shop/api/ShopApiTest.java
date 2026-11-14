package example.shop.api;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assumptions.assumeTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/**
 * REST API tests against the running app. The app's address comes from -DbaseUrl; without it
 * these tests are skipped.
 */
@Tag("api")
class ShopApiTest {
    private static final HttpClient HTTP = HttpClient.newHttpClient();
    private static final ObjectMapper JSON = new ObjectMapper();
    private static String baseUrl;

    @BeforeAll
    static void needsBaseUrl() {
        baseUrl = System.getProperty("baseUrl");
        assumeTrue(baseUrl != null && !baseUrl.isBlank(), "set -DbaseUrl to run API tests");
    }

    private static HttpResponse<String> get(String path) throws Exception {
        HttpRequest request = HttpRequest.newBuilder(URI.create(baseUrl + path)).GET().build();
        return HTTP.send(request, HttpResponse.BodyHandlers.ofString());
    }

    private static HttpResponse<String> postOrder(String productId, int quantity) throws Exception {
        String body = JSON.writeValueAsString(
                java.util.Map.of("productId", productId, "quantity", quantity));
        HttpRequest request = HttpRequest.newBuilder(URI.create(baseUrl + "/orders"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();
        return HTTP.send(request, HttpResponse.BodyHandlers.ofString());
    }

    @Test
    void readsAProduct() throws Exception {
        HttpResponse<String> response = get("/products/pen");

        assertEquals(200, response.statusCode());
        assertEquals("Pen", JSON.readTree(response.body()).get("name").asText());
    }

    @Test
    void unknownProductIs404() throws Exception {
        assertEquals(404, get("/products/nothing").statusCode());
    }

    @Test
    void placesAnOrderAndReadsItBack() throws Exception {
        HttpResponse<String> placed = postOrder("pen", 2);

        assertEquals(201, placed.statusCode());
        JsonNode order = JSON.readTree(placed.body());
        assertEquals(500, order.get("totalCents").asLong());
        HttpResponse<String> read = get("/orders/" + order.get("id").asLong());
        assertEquals(200, read.statusCode());
    }

    @Test
    void tooManyItemsIs409() throws Exception {
        HttpResponse<String> response = postOrder("chair", 9);

        assertEquals(409, response.statusCode());
        assertTrue(response.body().contains("in stock"));
    }
}
