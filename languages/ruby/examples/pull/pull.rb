# frozen_string_literal: true

require "net/http"
require "json"
require "uri"

# CPCP pull example: read access. Stdlib only.
#
# Adapted from the pod's Ruby callers (Net::HTTP#request parses the body
# regardless of status). Reads a method result without changing anything.
#
# Usage:
#   CPCP_URL=http://localhost:13002/_cpcp ruby pull.rb [method] [params-json]
#
# A non-200 status still carries the envelope: parse res.body on every
# status. Helpers that raise on 4xx (Net::HTTP.get, Faraday raise_error)
# lose the far side's reason.
BASE = "http://localhost:13002/_cpcp"

def pull(base_url, method, params = {})
  uri = URI.parse("#{base_url.sub(%r{/\z}, "")}/rpc")
  req = Net::HTTP::Post.new(uri)
  req["Content-Type"] = "application/json"
  req.body = JSON.generate("jsonrpc" => "2.0", "id" => 1, "method" => method, "params" => params)
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
  method = ARGV[0] || "note.list"
  params = ARGV[1] ? JSON.parse(ARGV[1]) : {}
  status, env = pull(base, method, params)
  puts JSON.pretty_generate("status" => status, "envelope" => env)
  exit(env["ok"] == true ? 0 : 1)
end
