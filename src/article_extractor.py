import requests
from bs4 import BeautifulSoup
from .url_validator import validate_public_http_url


def extract_article(url, timeout=12, max_bytes=2000000, max_redirects=5):
    """Retrieve readable article text while validating every redirect destination.

    Some publishers redirect canonical URLs (for example, to a regional or www URL).
    Follow those redirects only after validating each destination to avoid unsafe requests.
    """
    current_url = url
    response = None
    for _ in range(max_redirects + 1):
        ok, reason = validate_public_http_url(current_url, resolve_dns=True)
        if not ok:
            raise ValueError(reason)
        response = requests.get(
            current_url, timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; NewsPilotAI/1.0; +https://streamlit.io)'},
            stream=True, allow_redirects=False
        )
        if response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get('Location')
            response.close()
            if not location:
                raise ValueError('Publisher returned a redirect without a destination')
            from urllib.parse import urljoin
            current_url = urljoin(current_url, location)
            continue
        break
    else:
        raise ValueError('Too many publisher redirects')

    if response is None:
        raise ValueError('Could not retrieve publisher response')
    response.raise_for_status()
    ctype = response.headers.get('Content-Type', '').lower()
    if 'text/html' not in ctype:
        response.close()
        raise ValueError('Publisher response is not HTML')
    data = bytearray()
    try:
        for chunk in response.iter_content(65536):
            data.extend(chunk)
            if len(data) > max_bytes:
                raise ValueError('Article exceeds configured size limit')
    finally:
        response.close()
    soup = BeautifulSoup(bytes(data), 'html.parser')
    for tag in soup(['script', 'style', 'noscript', 'nav', 'footer', 'header']):
        tag.decompose()
    main = soup.find('article') or soup.find('main') or soup.body or soup
    text = ' '.join(main.get_text(' ', strip=True).split())
    if len(text) < 180:
        # trafilatura handles common publisher layouts better than generic HTML text extraction.
        try:
            import trafilatura
            extracted = trafilatura.extract(bytes(data).decode('utf-8', errors='replace'), include_comments=False, include_tables=False)
            if extracted and len(extracted.strip()) > len(text):
                text = ' '.join(extracted.split())
        except Exception:
            pass
    if len(text) < 180:
        raise ValueError('The page loaded, but readable article text was not found. The publisher may use a paywall or client-side rendering.')
    return text[:100000]
