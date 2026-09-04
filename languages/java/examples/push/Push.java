import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.HexFormat;
import java.security.SecureRandom;

/**
 * CPCP push example: write access. Stdlib only (java.net.http).
 *
 * <p>A PUSH names its intent before performing it. This example WRITES to
 * the backend -- point CPCP_URL at your own pod. Java ships no JSON
 * parser: the full body always prints; add a library for production.
 *
 * <p>Usage:
 * CPCP_URL=http://localhost:13002/_cpcp java Push.java [title] [operation-id]
 */
public class Push {
    static final String BASE = "http://localhost:13002/_cpcp";

    public static void main(String[] args) throws Exception {
        String base = System.getenv().getOrDefault("CPCP_URL", BASE);
        String title = args.length > 0 ? args[0] : "hello from cpcp";
        byte[] rand = new byte[8];
        new SecureRandom().nextBytes(rand);
        String op = args.length > 1 ? args[1] : "example-" + HexFormat.of().formatHex(rand);
        String body = "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"note.create\","
                + "\"params\":{\"title\":\"" + title.replace("\"", "\\\"") + "\","
                + "\"body\":\"posted by the CPCP push example\"},"
                + "\"operationId\":\"" + op + "\"}";

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
