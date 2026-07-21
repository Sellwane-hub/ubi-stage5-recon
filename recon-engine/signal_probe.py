"""Signal-service parser: talks to the line-protocol service and extracts the
virtual host and route key needed to unlock the HTTP service.

The service answers one command per connection then closes, so each command
uses a fresh connection through the scope-enforcing SafeRequester. Commands are
DISCOVERED via CAPS rather than assumed, and values are parsed by structure.
"""

from net import ScopeViolation


def _read_line(sock):
    """Read a single CRLF-terminated line from a socket and return it stripped."""
    data = b""
    while b"\n" not in data and len(data) < 4096:
        chunk = sock.recv(256)
        if not chunk:
            break
        data += chunk
    return data.decode("utf-8", errors="replace").strip()


def send_command(requester, host, port, command):
    """Open a fresh connection, read the banner, send one command, read reply.

    Returns (banner, reply). Raises ScopeViolation if the target is out of scope.
    """
    sock = requester.open_connection(host, port, "signal", command)
    try:
        banner = _read_line(sock)
        sock.sendall((command + "\r\n").encode("utf-8"))
        reply = _read_line(sock)
    finally:
        sock.close()
    return banner, reply


def parse_kv(line):
    """Parse a 'key=value; key=value' line into a dict, tolerant of spacing."""
    result = {}
    for part in line.split(";"):
        part = part.strip()
        if "=" in part:
            key, _, value = part.partition("=")
            result[key.strip()] = value.strip()
    return result


def discover_signal(requester, host, port):
    """Run the signal discovery chain: banner -> CAPS -> ROUTE.

    Returns a dict with banner, advertised commands, vhost, and route_key.
    """
    result = {"host": host, "port": port, "commands": [], "vhost": None, "route_key": None}

    banner, caps_reply = send_command(requester, host, port, "CAPS")
    result["banner"] = banner
    caps = parse_kv(caps_reply)
    if "commands" in caps:
        result["commands"] = [c.strip() for c in caps["commands"].split(",")]

    if "ROUTE" in result["commands"]:
        _, route_reply = send_command(requester, host, port, "ROUTE")
        route = parse_kv(route_reply)
        result["vhost"] = route.get("route")
        result["route_key"] = route.get("proof")

    return result
