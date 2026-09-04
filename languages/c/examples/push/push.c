/* CPCP push example: write access. C99 + POSIX sockets, no dependencies.
 *
 * A PUSH names its intent before performing it. This example WRITES to the
 * backend -- point CPCP_URL at your own pod. Same minimal HTTP/JSON
 * discipline as pull.c: envelope in, full body out, ok-scan for the exit
 * code. Only plain http://host[:port]/path URLs (no TLS).
 *
 * Usage:
 *   cc -O2 -o push push.c && CPCP_URL=http://localhost:13002/_cpcp ./push [title] [operation-id]
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <netdb.h>
#include <sys/socket.h>
#include <time.h>

#define BASE "http://localhost:13002/_cpcp"
#define CAP (256 * 1024)

static int split_url(const char *url, char *host, size_t hn, char *port, size_t pn, char *path, size_t qn) {
    const char *p = url;
    if (strncmp(p, "http://", 7) == 0) p += 7;
    const char *slash = strchr(p, '/');
    size_t hostlen = slash ? (size_t)(slash - p) : strlen(p);
    const char *colon = memchr(p, ':', hostlen);
    if (colon) {
        if ((size_t)(colon - p) >= hn) return -1;
        memcpy(host, p, (size_t)(colon - p));
        host[colon - p] = '\0';
        size_t plen = hostlen - (size_t)(colon - p) - 1;
        if (plen >= pn) return -1;
        memcpy(port, colon + 1, plen);
        port[plen] = '\0';
    } else {
        if (hostlen >= hn) return -1;
        memcpy(host, p, hostlen);
        host[hostlen] = '\0';
        strcpy(port, "80");
    }
    const char *pp = slash ? slash : "/";
    size_t plen = strlen(pp);
    while (plen > 1 && pp[plen - 1] == '/') plen--;
    int is_rpc = plen >= 4 && strncmp(pp + plen - 4, "/rpc", 4) == 0;
    char full[1024];
    if (is_rpc)
        snprintf(full, sizeof full, "%.*s", (int)plen, pp);
    else
        snprintf(full, sizeof full, "%.*s/rpc", (int)plen, pp);
    if (strlen(full) >= qn) return -1;
    strcpy(path, full);
    return 0;
}

int main(int argc, char **argv) {
    const char *env = getenv("CPCP_URL");
    const char *base = (env && *env) ? env : BASE;
    const char *title = argc > 1 ? argv[1] : "hello from cpcp";
    char host[256], port[16], path[1024];
    if (split_url(base, host, sizeof host, port, sizeof port, path, sizeof path) != 0) {
        printf("{\"status\": 0, \"ok\": false, \"reason\": \"bad_url\"}\n");
        return 1;
    }
    char opid[64];
    if (argc > 2) {
        snprintf(opid, sizeof opid, "%s", argv[2]);
    } else {
        srand((unsigned)(time(0) ^ getpid()));
        snprintf(opid, sizeof opid, "example-%08x%08x", rand(), rand());
    }
    char payload[2048];
    snprintf(payload, sizeof payload,
             "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"note.create\","
             "\"params\":{\"title\":\"%.1500s\",\"body\":\"posted by the CPCP push example\"},\"operationId\":\"%.63s\"}",
             title, opid);
    char req[8192];
    snprintf(req, sizeof req,
             "POST %s HTTP/1.1\r\nHost: %s\r\nContent-Type: application/json\r\nContent-Length: %lu\r\nConnection: close\r\n\r\n%s",
             path, host, (unsigned long)strlen(payload), payload);

    struct addrinfo hints, *addrs;
    memset(&hints, 0, sizeof hints);
    hints.ai_socktype = SOCK_STREAM;
    if (getaddrinfo(host, port, &hints, &addrs) != 0) {
        printf("{\"status\": 0, \"ok\": false, \"reason\": \"unreachable\"}\n");
        return 1;
    }
    int fd = -1;
    for (struct addrinfo *a = addrs; a; a = a->ai_next) {
        fd = socket(a->ai_family, a->ai_socktype, a->ai_protocol);
        if (fd < 0) continue;
        if (connect(fd, a->ai_addr, a->ai_addrlen) == 0) break;
        close(fd);
        fd = -1;
    }
    freeaddrinfo(addrs);
    if (fd < 0) {
        printf("{\"status\": 0, \"ok\": false, \"reason\": \"unreachable\"}\n");
        return 1;
    }
    size_t off = 0, len = strlen(req);
    while (off < len) {
        ssize_t n = write(fd, req + off, len - off);
        if (n <= 0) break;
        off += (size_t)n;
    }
    static char buf[CAP];
    size_t total = 0;
    ssize_t n;
    while (total < sizeof(buf) - 1 && (n = read(fd, buf + total, sizeof(buf) - 1 - total)) > 0)
        total += (size_t)n;
    close(fd);
    buf[total] = '\0';
    int status = 0;
    sscanf(buf, "HTTP/%*s %d", &status);
    char *body = strstr(buf, "\r\n\r\n");
    body = body ? body + 4 : buf;
    int ok = strstr(body, "\"ok\":true") != NULL || strstr(body, "\"ok\": true") != NULL;
    printf("{\"status\": %d, \"body\": %s}\n", status, *body ? body : "{}");
    return ok ? 0 : 1;
}
