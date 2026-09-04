# Java examples

Stdlib only (`java.net.http`, Java 11+). Single-file programs — `java
Pull.java` runs directly, no build file. No JSON library ships with the
JDK: the full body always prints and success reads from the `"ok":true`
marker. Add a JSON library for production; the transport discipline does
not change.

* `pull/Pull.java` — read access. `CPCP_URL=... java Pull.java [method]`
* `push/Push.java` — write access. `CPCP_URL=... java Push.java [title] [operation-id]`
  (**writes to the backend** — point at your own pod).
