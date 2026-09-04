// CPCP push example: write access. Stdlib only (net/http, encoding/json,
// crypto/rand).
//
// A PUSH names its intent before performing it: asking twice with the same
// name must not perform it twice. This example WRITES to the backend --
// point CPCP_URL at your own pod.
//
// Usage:
//
//	CPCP_URL=http://localhost:13002/_cpcp go run push.go [method] [params-json] [operation-id]
package main

import (
	"bytes"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
	"time"
)

func operationID() string {
	var b [8]byte
	if _, err := rand.Read(b[:]); err != nil {
		return "example-fallback"
	}
	return "example-" + hex.EncodeToString(b[:])
}

func push(baseURL, method string, params map[string]any, op string) (int, map[string]any) {
	if op == "" {
		op = operationID()
	}
	// Trailing slashes must not double the path: every client normalizes
	// the seam root before appending /rpc.
	baseURL = strings.TrimRight(baseURL, "/")
	body, _ := json.Marshal(map[string]any{
		"jsonrpc": "2.0", "id": 1, "method": method, "params": params, "operationId": op,
	})
	client := &http.Client{Timeout: 30 * time.Second}
	req, err := http.NewRequest("POST", baseURL+"/rpc", bytes.NewReader(body))
	if err != nil {
		return 0, map[string]any{"ok": false, "reason": "unreachable", "because": err.Error()}
	}
	req.Header.Set("Content-Type", "application/json")
	res, err := client.Do(req)
	if err != nil {
		return 0, map[string]any{"ok": false, "reason": "unreachable", "because": err.Error()}
	}
	defer res.Body.Close()
	var env map[string]any
	if err := json.NewDecoder(res.Body).Decode(&env); err != nil {
		return res.StatusCode, map[string]any{"ok": false, "reason": "cpcp_unparseable", "because": "no JSON body"}
	}
	return res.StatusCode, env
}

func main() {
	base := os.Getenv("CPCP_URL")
	if base == "" {
		base = "http://localhost:13002/_cpcp"
	}
	method := "note.create"
	if len(os.Args) > 1 {
		method = os.Args[1]
	}
	params := map[string]any{"title": "hello from cpcp", "body": "posted by the CPCP push example"}
	if len(os.Args) > 2 {
		params = map[string]any{}
		if err := json.Unmarshal([]byte(os.Args[2]), &params); err != nil {
			fmt.Fprintln(os.Stderr, "params must be JSON")
			os.Exit(2)
		}
	}
	op := ""
	if len(os.Args) > 3 {
		op = os.Args[3]
	}
	status, env := push(base, method, params, op)
	out, _ := json.MarshalIndent(map[string]any{"status": status, "envelope": env}, "", "  ")
	fmt.Println(string(out))
	if env["ok"] != true {
		os.Exit(1)
	}
}
