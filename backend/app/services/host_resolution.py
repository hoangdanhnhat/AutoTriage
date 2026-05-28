import ipaddress
import logging
import socket
from functools import lru_cache

logger = logging.getLogger(__name__)


def is_ip_address(value: str | None) -> bool:
    if not value:
        return False
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return True


@lru_cache(maxsize=2048)
def resolve_hostname_to_ip(hostname: str) -> str | None:
    try:
        addr_info = socket.getaddrinfo(hostname, None, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        logger.info("Unable to resolve hostname %s to an IP address: %s", hostname, exc)
        return None
    except OSError as exc:
        logger.warning("Unexpected error resolving hostname %s to an IP address: %s", hostname, exc)
        return None

    for family, _, _, _, sockaddr in addr_info:
        ip = sockaddr[0]
        if family == socket.AF_INET:
            return ip

    if addr_info:
        return addr_info[0][4][0]
    return None


@lru_cache(maxsize=2048)
def resolve_ip_to_hostname(ip_address: str) -> str | None:
    try:
        hostname, _, _ = socket.gethostbyaddr(ip_address)
    except socket.herror as exc:
        logger.info("Unable to resolve IP address %s to a hostname: %s", ip_address, exc)
        return None
    except OSError as exc:
        logger.warning("Unexpected error resolving IP address %s to a hostname: %s", ip_address, exc)
        return None
    return hostname


def normalize_host_identity(ip_address: str, hostname: str | None = None) -> tuple[str, str | None]:
    """
    Return best-effort (ip_address, hostname) for a host token.

    Inventories may contain either bare IPs or bare hostnames. DNS lookup failures
    should not block inventory import or API responses, so unresolved values are
    preserved instead of raising.
    """
    if is_ip_address(ip_address):
        return ip_address, hostname or resolve_ip_to_hostname(ip_address)

    original_hostname = hostname or ip_address
    resolved_ip = resolve_hostname_to_ip(original_hostname)
    return resolved_ip or ip_address, original_hostname
