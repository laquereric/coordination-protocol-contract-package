import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

/**
 * CPCP pull example: read access. Stdlib only (java.net.http).
 *
 * <p>Java ships no JSON parser: the full body always prints, and success
 * is read from the {@code "ok":true} marker. For production parsing add a
 * JSON library; the transport discipline below does not change.
 *
 * <p>Usage:
 * CPCP_URL=http://localhost:13002/_cpcp java Pull.java [method]
 *
 * <p>A non-200 status still carries the envelope: the body is read on
 * every status. Never mistake transport failure for a refusal.
 */
public class Pull {
    static final String BASE = "http://localhost:13002/_cpcp";

    public static void main(String[] args) throws Exception {
        String base = System.getenv().getOrDefault("CPCP_URL", BASE);
        String method = args.length > 0 ? args[0] : "note.list";
        String body = "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"" + method + "\",\"params\":{}}";

        HttpClient client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(5)).build();
        int status;
        String text;
        try {
            HttpResponse<String> res = client.send(
                    HttpRequest.newBuilder(URI.create(base + "/rpc"))
                            .timeout(Duration.ofSeconds(30))
                            .header("Content-Type", "application/json")
                            .POST(HttpRequest.BodyPublishers.ofString(body))
                            .build(),
                    HttpResponse.BodyHandlers.ofString());
            status = res.statusCode();
            text = res.body();
        } catch (Exception e) {
            System.out.println("{\"status\": 0, \"ok\": false, \"reason\": \"unreachable\"}");
            System.exit(1);
            return;
        }
        boolean ok = text.contains("\"ok\":true") || text.contains("\"ok\": true");
        System.out.println("{\"status\": " + status + ", \"body\": " + text + "}");
        System.exit(ok ? 0 : 1);
    }
}
