"""HTTP/vhost prober: retrieves HTTP responses over a raw socket (stdlib only)
and applies wildcard baselining to confirm the genuine virtual host.

It establishes a baseline using a random, non-existent hostname, then probes
the real vhost and compares. Responses matching the wildcard baseline are
suppressed; a differing response confirms genuine content. It retrieves the
diagnostics data needed for the foothold but never fetches the flag itself.
"""

import secrets

from baseline import response_signature, classify


def _recv_all(sock):
    """Read the full response from a socket until the peer closes it."""
    chunks = []
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks)


def parse_http_response(raw):
    """Split a raw HTTP response into (status_code, headers dict, body str)."""
    head, _, body = raw.partition(b"\r\n\r\n")
    lines = head.decode("utf-8", errors="replace").split("\r\n")
    status_line = lines[0] if lines else ""
    parts = status_line.split(" ", 2)
    status = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    headers = {}
    for line in lines[1:]:
        if ":" in line:
            key, _, value = line.partition(":")
            headers[key.strip().lower()] = value.strip()
    return status, headers, body.decode("utf-8", errors="replace")


def http_get(requester, host, port, path, vhost, extra_headers=None):
    """Perform an HTTP GET for a given path and Host (vhost) over a raw socket.

    Returns (status, headers, body). Scope is enforced by open_connection.
    """
    sock = requester.open_connection(host, port, "http", path)
    try:
        request = [
            f"GET {path} HTTP/1.1",
            f"Host: {vhost}",
            "Connection: close",
        ]
        if extra_headers:
            for name, value in extra_headers.items():
                request.append(f"{name}: {value}")
        request.append("")
        request.append("")
        sock.sendall("\r\n".join(request).encode("utf-8"))
        raw = _recv_all(sock)
    finally:
        sock.close()
    return parse_http_response(raw)


def probe_http(requester, host, port, vhost):
    """Discover HTTP content behind the genuine vhost.

    1. Baseline with a random hostname (captures wildcard noise).
    2. Probe the real vhost root and compare -> confirm it is genuine.
    3. Fetch robots.txt and ops-diagnostics behind the real vhost.
    Returns a dict of observations including any discovered credentials.
    """
    result = {"vhost": vhost, "baseline_class": None, "paths": {}, "credentials": {}}

    # 1. baseline: a random hostname that should hit the wildcard catch-all
    fake_vhost = f"zz{secrets.token_hex(6)}.invalid"
    b_status, _, b_body = http_get(requester, host, port, "/", fake_vhost)
    baseline_sig = response_signature(b_status, b_body)

    # 2. real vhost root, compared against baseline
    r_status, _, r_body = http_get(requester, host, port, "/", vhost)
    candidate_sig = response_signature(r_status, r_body)
    result["baseline_class"] = classify(baseline_sig, candidate_sig)
    result["paths"]["/"] = {"status": r_status, "bytes": candidate_sig["bytes"]}

    # 3. fetch the real content behind the genuine vhost
    for path in ("/robots.txt", "/ops-diagnostics"):
        status, _, body = http_get(requester, host, port, path, vhost)
        result["paths"][path] = {"status": status, "bytes": len(body.encode("utf-8"))}
        if path == "/ops-diagnostics" and status == 200:
            import json
            try:
                data = json.loads(body)
                result["credentials"] = {
                    "username": data.get("support_user"),
                    "password": data.get("support_password"),
                }
            except json.JSONDecodeError:
                pass

    return result
