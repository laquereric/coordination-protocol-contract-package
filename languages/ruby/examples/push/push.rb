# frozen_string_literal: true

require "net/http"
require "json"
require "uri"
require "securerandom"

# CPCP push example: write access. Stdlib only.
#
# A PUSH names its intent before performing it: asking twice with the same
# name must not perform it twice. This example WRITES to the backend --
# point CPCP_URL at your own pod.
#
# Usage:
#   CPCP_URL=http://localhost:13002/_cpcp ruby push.rb [method] [params-json] [operation-id]
#   Defaults: note.create {"title": "hello from cpcp"} with a random operationId.
BASE = "http://localhost:13002/_cpcp"

def push(base_url, method, params = {}, operation_id = nil)
  op = operation_id || "example-#{SecureRandom.hex(8)}"
  uri = URI.parse("#{base_url.sub(%r{/\z}, "")}/rpc")
  req = Net::HTTP::Post.new(uri)
  req["Content-Type"] = "application/json"
  req.body = JSON.generate("jsonrpc" => "2.0", "id" => 1, "method" => method,
                           "params" => params, "operationId" => op)
  res = Net::HTTP.start(uri.hostname, uri.port, open_timeout: 5, read_timeout: 30) do |h|
    h.request(req)
  end
  envelope = begin
    JSON.parse(res.body.to_s)
  rescue JSON::ParserError
    { "raw" => res.body.to_s[0, 400] }
  end
  [res.code.to_i, envelope]
rescue StandardError => e
  [0, { "ok" => false, "reason" => "unreachable", "because" => "#{e.class}: #{e.message}" }]
end

if $PROGRAM_NAME == __FILE__
  base = ENV.fetch("CPCP_URL", BASE)
  method = ARGV[0] || "note.create"
  params = ARGV[1] ? JSON.parse(ARGV[1]) : { "title" => "hello from cpcp", "body" => "posted by the CPCP push example" }
  status, env = push(base, method, params, ARGV[2])
  puts JSON.pretty_generate("status" => status, "envelope" => env)
  exit(env["ok"] == true ? 0 : 1)
end
