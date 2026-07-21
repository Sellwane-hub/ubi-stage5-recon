"""Small decision helpers used by the engine and validated by published
fixtures: CIDR/hostname/port scope checks, DNS wildcard suppression, resume
checkpoint logic, and tool-failure fallback decisions.
"""

import ipaddress


def scope_cidr(scope_cidrs, candidate_ip):
    """allow if candidate_ip falls inside any scope CIDR, else deny."""
    ip = ipaddress.ip_address(candidate_ip)
    for cidr in scope_cidrs:
        if ip in ipaddress.ip_network(cidr, strict=False):
            return "allow"
    return "deny"


def scope_hostname(scope_hosts, candidate):
    """allow only if candidate hostname is explicitly in scope."""
    return "allow" if candidate in scope_hosts else "deny"


def scope_port(scope_ranges, candidate):
    """candidate like 'tcp/9443'; scope like ['tcp/1-9000']. allow if in range."""
    c_proto, _, c_port = candidate.partition("/")
    c_port = int(c_port)
    for rng in scope_ranges:
        proto, _, ports = rng.partition("/")
        if proto != c_proto:
            continue
        low, _, high = ports.partition("-")
        if int(low) <= c_port <= int(high or low):
            return "allow"
    return "deny"


def dns_wildcard(random_responses, candidate_response):
    """suppress if candidate matches the wildcard baseline, else retain."""
    wildcard_ips = set(random_responses)
    if candidate_response in wildcard_ips and len(wildcard_ips) == 1:
        return "suppress"
    return "retain"


def next_step(completed, pending):
    """Return the next pending step, or None if nothing is pending."""
    return pending[0] if pending else None


def tool_failure_decision(exit_code, fallback_available):
    """Decide what to do when an external tool exits nonzero."""
    if exit_code == 0:
        return "ok"
    return "fallback" if fallback_available else "nonzero_exit"
