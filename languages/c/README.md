# C examples

C99 plus POSIX sockets. No dependencies. The language ships no HTTP
client and no JSON parser, so these speak just enough HTTP/1.1 to POST
one envelope (Content-Length framing, status line) and scan the body for
the `ok` marker; the full body always prints. Only plain
`http://host[:port]/path` URLs (no TLS).

* `pull/pull.c` — read access. `cc -O2 -o pull pull.c && CPCP_URL=... ./pull [method]`
* `push/push.c` — write access. `cc -O2 -o push push.c && CPCP_URL=... ./push [title] [operation-id]`
  (**writes to the backend** — point at your own pod).
