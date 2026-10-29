from urllib.parse import urlparse
import ipaddress, socket

def validate_public_http_url(url: str, resolve_dns: bool = False) -> tuple[bool, str]:
    try:
        p=urlparse(url)
        if p.scheme not in ('http','https') or not p.hostname: return False, 'Only absolute HTTP(S) URLs are allowed'
        host=p.hostname.lower().rstrip('.')
        if host in ('localhost','localhost.localdomain') or host.endswith('.local'): return False, 'Local hostnames are blocked'
        try:
            ip=ipaddress.ip_address(host)
            if not ip.is_global: return False, 'Private, loopback, and non-public IPs are blocked'
        except ValueError: pass
        if resolve_dns:
            for item in socket.getaddrinfo(host, p.port or (443 if p.scheme=='https' else 80), type=socket.SOCK_STREAM):
                ip=ipaddress.ip_address(item[4][0])
                if not ip.is_global: return False, 'Hostname resolves to a non-public IP'
        return True, 'ok'
    except socket.gaierror as e: return False, f'DNS resolution failed: {e}'
    except Exception as e: return False, f'Malformed URL: {e}'
