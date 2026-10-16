import ipaddress
import socket
from typing import Tuple
from urllib.parse import urlparse
import httpx
from fastapi import HTTPException, status

# Disallowed internal/private networks
DISALLOWED_CIDRS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local / AWS metadata
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("224.0.0.0/4"),     # Multicast
    ipaddress.ip_network("240.0.0.0/4"),     # Reserved
    ipaddress.ip_network("::1/128"),         # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),        # IPv6 Unique Local
    ipaddress.ip_network("fe80::/10"),       # IPv6 Link-Local
]


def validate_url_safety(url: str) -> str:
    """
    Validates URL scheme, resolves hostname, and checks against private/internal IP ranges
    to prevent SSRF attacks.
    """
    if not url or not isinstance(url, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL must be a non-empty string.")

    url = url.strip()
    parsed = urlparse(url)

    if parsed.scheme.lower() not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported URL scheme '{parsed.scheme}'. Only http and https are permitted."
        )

    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid URL: Missing hostname.")

    # Prevent localhost explicitly
    if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to local loopback is prohibited.")

    # Resolve IP addresses for the hostname
    try:
        resolved_addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not resolve host '{hostname}'. Check the URL or your network connection."
        )

    for item in resolved_addr_info:
        ip_str = item[4][0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            for cidr in DISALLOWED_CIDRS:
                if ip_obj in cidr:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access to private/internal IP range ({ip_str}) is blocked by CapCheck security policy."
                    )
        except ValueError:
            continue

    return url


async def safe_fetch_url(url: str, max_bytes: int = 5 * 1024 * 1024, timeout_sec: float = 10.0) -> Tuple[str, str, int]:
    """
    Fetches the content of a public URL safely with size limits and SSRF re-checks.
    Returns (html_content, final_url, status_code).
    """
    safe_url = validate_url_safety(url)

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; CapCheck-AI/1.0; verification-research)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    async with httpx.AsyncClient(
        headers=headers,
        timeout=timeout_sec,
        follow_redirects=True,
        max_redirects=3,
        verify=True
    ) as client:
        try:
            response = await client.get(safe_url)
            # Re-check final redirected URL
            validate_url_safety(str(response.url))

            if response.status_code >= 400:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Target web server responded with HTTP {response.status_code} ({response.reason_phrase})."
                )

            # Enforce size limit
            content_bytes = response.content
            if len(content_bytes) > max_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Target page exceeded maximum allowed download size (5MB)."
                )

            return response.text, str(response.url), response.status_code
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Request to target URL timed out."
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch content from URL: {str(e)}"
            )
