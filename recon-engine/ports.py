"""Port prober: discovers which authorized ports are open.

Every connection attempt goes through SafeRequester, so scope is enforced and
logged for each probe. The decoy and any non-IN port are refused before a
socket is ever created, so this prober cannot touch them.
"""

import socket

from net import ScopeViolation


def probe_ports(requester, host, ports):
    """Try to connect to each port. Return a list of findings.

    Each finding is a dict: host, port, transport, state ('open' or 'closed'),
    and any error note. Ports refused by scope are reported as 'refused'.
    """
    findings = []
    for port in ports:
        try:
            sock = requester.open_connection(host, port, "tcp", "connect")
            sock.close()
            findings.append({
                "host": host,
                "port": port,
                "transport": "tcp",
                "state": "open",
                "note": "",
            })
        except ScopeViolation as exc:
            findings.append({
                "host": host,
                "port": port,
                "transport": "tcp",
                "state": "refused",
                "note": str(exc),
            })
        except (ConnectionRefusedError, socket.timeout, OSError) as exc:
            findings.append({
                "host": host,
                "port": port,
                "transport": "tcp",
                "state": "closed",
                "note": type(exc).__name__,
            })
    return findings
