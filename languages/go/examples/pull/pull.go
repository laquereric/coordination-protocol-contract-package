// CPCP pull example: read access. Stdlib only (net/http, encoding/json).
//
// Usage:
//
//	CPCP_URL=http://localhost:13002/_cpcp go run pull.go [method] [params-json]
//
// A non-200 status still carries the envelope: the body is decoded on
// every status. Never mistake transport failure for a refusal.
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
	"time"
)

func pull(baseURL, method string, params map[string]any) (int, map[string]any) {
	// Trailing slashes must not double the path: every client normalizes
	// the seam root before appending /rpc.
	baseURL = strings.TrimRight(baseURL, "/")
	body, _ := json.Marshal(map[string]any{
		"jsonrpc": "2.0", "id": 1, "method": method, "params": params,
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
	method := "note.list"
	if len(os.Args) > 1 {
		method = os.Args[1]
	}
	params := map[string]any{}
	if len(os.Args) > 2 {
		if err := json.Unmarshal([]byte(os.Args[2]), &params); err != nil {
			fmt.Fprintln(os.Stderr, "params must be JSON")
			os.Exit(2)
		}
	}
	status, env := pull(base, method, params)
	out, _ := json.MarshalIndent(map[string]any{"status": status, "envelope": env}, "", "  ")
	fmt.Println(string(out))
	if env["ok"] != true {
		os.Exit(1)
	}
}
