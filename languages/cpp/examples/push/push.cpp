// CPCP push example: write access. C++17, POSIX sockets, no dependencies.
//
// A PUSH names its intent before performing it. This example WRITES to the
// backend -- point CPCP_URL at your own pod. Same minimal discipline as
// pull.cpp.
//
// Usage:
//   c++ -O2 -std=c++17 -o push push.cpp && CPCP_URL=http://localhost:13002/_cpcp ./push [title] [operation-id]
//
// Only plain http://host[:port]/path URLs (no TLS).
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <string>
#include <netdb.h>
#include <unistd.h>
#include <sys/socket.h>

namespace {

const char *kBase = "http://localhost:13002/_cpcp";
const size_t kCap = 256 * 1024;

bool split_url(const std::string &url, std::string &host, std::string &port, std::string &path) {
    std::string p = url;
    const std::string scheme = "http://";
    if (p.compare(0, scheme.size(), scheme) == 0) p = p.substr(scheme.size());
    size_t slash = p.find('/');
    std::string authority = slash == std::string::npos ? p : p.substr(0, slash);
    size_t colon = authority.find(':');
    if (colon == std::string::npos) {
        host = authority;
        port = "80";
    } else {
        host = authority.substr(0, colon);
        port = authority.substr(colon + 1);
    }
    std::string pp = slash == std::string::npos ? "/" : p.substr(slash);
    while (pp.size() > 1 && pp.back() == '/') pp.pop_back();
    const std::string rpc = "/rpc";
    path = (pp.size() >= rpc.size() && pp.compare(pp.size() - rpc.size(), rpc.size(), rpc) == 0)
        ? pp : pp + rpc;
    return !host.empty();
}

std::string escape_json(const std::string &in) {
    std::string out;
    for (char c : in) {
        if (c == '"') out += "\\\"";
        else if (c == '\\') out += "\\\\";
        else if (c == '\n') out += "\\n";
        else out += c;
    }
    return out;
}

int post(const std::string &base, const std::string &payload) {
    std::string host, port, path;
    if (!split_url(base, host, port, path)) {
        printf("{\"status\": 0, \"ok\": false, \"reason\": \"bad_url\"}\n");
        return 1;
    }
    std::string req = "POST " + path + " HTTP/1.1\r\nHost: " + host +
        "\r\nContent-Type: application/json\r\nContent-Length: " + std::to_string(payload.size()) +
        "\r\nConnection: close\r\n\r\n" + payload;

    addrinfo hints{};
    hints.ai_socktype = SOCK_STREAM;
    addrinfo *addrs = nullptr;
    if (getaddrinfo(host.c_str(), port.c_str(), &hints, &addrs) != 0) {
        printf("{\"status\": 0, \"ok\": false, \"reason\": \"unreachable\"}\n");
        return 1;
    }
    int fd = -1;
    for (addrinfo *a = addrs; a; a = a->ai_next) {
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
    size_t off = 0;
    while (off < req.size()) {
        ssize_t n = write(fd, req.data() + off, req.size() - off);
        if (n <= 0) break;
        off += (size_t)n;
    }
    std::string buf;
    buf.resize(kCap);
    size_t total = 0;
    ssize_t n;
    while (total < kCap - 1 && (n = read(fd, &buf[total], kCap - 1 - total)) > 0)
        total += (size_t)n;
    close(fd);
    buf.resize(total);
    int status = 0;
    sscanf(buf.c_str(), "HTTP/%*s %d", &status);
    size_t hdr = buf.find("\r\n\r\n");
    std::string body = hdr == std::string::npos ? buf : buf.substr(hdr + 4);
    bool ok = body.find("\"ok\":true") != std::string::npos ||
              body.find("\"ok\": true") != std::string::npos;
    printf("{\"status\": %d, \"body\": %s}\n", status, body.empty() ? "{}" : body.c_str());
    return ok ? 0 : 1;
}

}  // namespace

int main(int argc, char **argv) {
    const char *env = getenv("CPCP_URL");
    std::string base = (env && *env) ? env : kBase;
    std::string title = argc > 1 ? argv[1] : "hello from cpcp";
    char opid[64];
    if (argc > 2) {
        snprintf(opid, sizeof opid, "%s", argv[2]);
    } else {
        snprintf(opid, sizeof opid, "example-%lx%lx",
                 (unsigned long)time(nullptr), (unsigned long)getpid());
    }
    std::string payload =
        "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"note.create\","
        "\"params\":{\"title\":\"" + escape_json(title) +
        "\",\"body\":\"posted by the CPCP push example\"},"
        "\"operationId\":\"" + std::string(opid) + "\"}";
    return post(base, payload);
}
