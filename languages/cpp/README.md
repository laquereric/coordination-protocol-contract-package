# C++ examples

C++17 plus POSIX sockets. No dependencies. Same minimal discipline as
the C twins with `std::string` handling: POST one envelope, print status
plus full body, scan for the `ok` marker. Only plain
`http://host[:port]/path` URLs (no TLS).

* `pull/pull.cpp` — read access. `c++ -O2 -std=c++17 -o pull pull.cpp && CPCP_URL=... ./pull [method]`
* `push/push.cpp` — write access. `c++ -O2 -std=c++17 -o push push.cpp && CPCP_URL=... ./push [title] [operation-id]`
  (**writes to the backend** — point at your own pod).
