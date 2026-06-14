from __future__ import annotations

from dataclasses import dataclass
import ipaddress


DOCUMENTATION_NETWORKS = (
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("2001:db8::/32"),
)


@dataclass(frozen=True)
class IPContext:
    address: str
    is_valid: bool
    version: int | None
    category: str
    is_global: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "address": self.address,
            "is_valid": self.is_valid,
            "version": self.version,
            "category": self.category,
            "is_global": self.is_global,
            "reason": self.reason,
        }


def classify_ip_address(address: str) -> IPContext:
    try:
        ip_obj = ipaddress.ip_address(address)
    except ValueError:
        return IPContext(
            address=address,
            is_valid=False,
            version=None,
            category="invalid",
            is_global=False,
            reason="Invalid IP address format.",
        )

    if any(ip_obj in network for network in DOCUMENTATION_NETWORKS):
        return IPContext(address, True, ip_obj.version, "documentation", False, "Documentation or test address range.")
    if ip_obj.is_private:
        return IPContext(address, True, ip_obj.version, "private", False, "Private address used inside local networks.")
    if ip_obj.is_loopback:
        return IPContext(address, True, ip_obj.version, "loopback", False, "Loopback address reserved for local host use.")
    if ip_obj.is_link_local:
        return IPContext(address, True, ip_obj.version, "link-local", False, "Link-local address reserved for local network discovery.")
    if ip_obj.is_multicast:
        return IPContext(address, True, ip_obj.version, "multicast", False, "Multicast address is not globally routable.")
    if ip_obj.is_unspecified:
        return IPContext(address, True, ip_obj.version, "unspecified", False, "Unspecified address is not a routable source.")
    if ip_obj.is_reserved:
        return IPContext(address, True, ip_obj.version, "reserved", False, "Reserved address range is not globally routable.")
    if not ip_obj.is_global:
        return IPContext(address, True, ip_obj.version, "documentation", False, "Documentation or special-use address range.")

    return IPContext(
        address=address,
        is_valid=True,
        version=ip_obj.version,
        category="global",
        is_global=True,
        reason="Globally routable public source address.",
    )
