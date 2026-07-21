"""Parser adapters: convert external tool output (nmap XML, naabu/httpx JSON,
line format) into one versioned schema, WITHOUT shell-string concatenation.

Adapters parse by structure and fail safely with specific, named errors rather
than crashing or silently accepting malformed input. These feed the same
normalized records as the native probers, so an optional external tool can be
swapped in or out without changing downstream logic.
"""

import json
import xml.etree.ElementTree as ET


class ParseError(Exception):
    """Raised with a specific code when tool output cannot be parsed."""
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def parse_nmap_xml(text):
    """Parse a single nmap <host> XML snippet into a normalized-ish dict."""
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        raise ParseError("MALFORMED_TOOL_OUTPUT")
    address = root.find("address")
    port = root.find(".//port")
    if address is None or port is None:
        raise ParseError("REQUIRED_FIELD_MISSING")
    state = port.find("state")
    service = port.find("service")
    return {
        "host": address.get("addr"),
        "port": int(port.get("portid")),
        "transport": port.get("protocol"),
        "service": service.get("name") if service is not None else None,
        "state": state.get("state") if state is not None else None,
    }


def parse_naabu_json(obj):
    """Parse naabu JSON (dict or JSON string) into a normalized-ish dict."""
    data = _as_obj(obj)
    if "port" not in data:
        raise ParseError("REQUIRED_FIELD_MISSING")
    return {
        "host": data.get("host"),
        "ip": data.get("ip"),
        "port": int(data["port"]),
        "transport": data.get("protocol", "tcp"),
    }


def parse_httpx_json(obj):
    """Parse httpx JSON into scheme/host/port/status."""
    data = _as_obj(obj)
    url = data.get("url", "")
    scheme, _, rest = url.partition("://")
    hostport = rest.split("/", 1)[0]
    host, _, port = hostport.partition(":")
    if not port:
        port = "443" if scheme == "https" else "80"
    return {
        "scheme": scheme,
        "host": host,
        "port": int(port),
        "status": data.get("status_code"),
    }


def parse_line(text):
    """Parse a line like '192.0.2.12:8022 ssh OpenSSH_9.2'."""
    parts = text.split()
    if not parts or ":" not in parts[0]:
        raise ParseError("MALFORMED_TOOL_OUTPUT")
    ip, _, port = parts[0].partition(":")
    if not port.isdigit():
        raise ParseError("REQUIRED_FIELD_MISSING")
    return {
        "ip": ip,
        "port": int(port),
        "service": parts[1] if len(parts) > 1 else None,
        "product": parts[2] if len(parts) > 2 else None,
    }


def _as_obj(obj):
    """Accept a dict directly, or parse a JSON string; raise on malformed JSON."""
    if isinstance(obj, dict):
        return obj
    try:
        return json.loads(obj)
    except (json.JSONDecodeError, TypeError):
        raise ParseError("MALFORMED_TOOL_OUTPUT")
