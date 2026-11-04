"""Extract article prose conservatively; reject navigation, sitemap and boilerplate pages."""
import re
import requests
from bs4 import BeautifulSoup
from .url_validator import validate_public_http_url

_BOILERPLATE = (
    'advanced search', 'subscribe', 'newsletter', 'sitemap', 'sign in',
    'log in', 'cookie policy', 'privacy policy', 'terms of use',
    'all rights reserved', 'read the latest edition', 'advertisement',
    'skip to content', 'menu', 'home page', 'contact us',
)


def _normalise(text):
    return re.sub(r'\s+', ' ', str(text or '')).strip()


def _is_boilerplate(text):
    low = text.casefold()
    hits = sum(1 for phrase in _BOILERPLATE if phrase in low)
    words = low.split()
    # A page dominated by navigation labels or subscription prompts is not an article.
    return hits >= 2 or (hits >= 1 and len(words) < 100)


def _usable_article_text(text):
    text = _normalise(text)
    if len(text) < 250 or _is_boilerplate(text):
        return False
    sentences = re.findall(r'[^.!?]{35,}[.!?]', text)
    words = re.findall(r"[A-Za-z][A-Za-z'-]+", text)
    if len(sentences) < 3 or len(words) < 45:
        return False
    # Reject pages that look like a list of links/headlines rather than prose.
    short_fragments = [part for part in re.split(r'\s{2,}|\s[|•]\s', text) if len(part.split()) < 5]
    if len(short_fragments) >= 5:
        return False
    return True


def extract_article(url, timeout=12, max_bytes=2000000, max_redirects=5):
    """Fetch a public article URL and return only plausible article body text.

    Redirects are validated individually. Extraction favours precision: when a
    publisher page exposes only navigation, sitemap or subscription text, fail
    explicitly rather than passing that junk into summaries or graphics.
    """
    current_url = url
    response = None
    for _ in range(max_redirects + 1):
        ok, reason = validate_public_http_url(current_url, resolve_dns=True)
        if not ok:
            raise ValueError(f'Unsafe or invalid publisher URL: {reason}')
        response = requests.get(
            current_url, timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36'},
            stream=True, allow_redirects=False,
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
        raise ValueError('No response received from publisher')
    try:
        response.raise_for_status()
        ctype = response.headers.get('Content-Type', '').lower()
        if 'text/html' not in ctype and 'application/xhtml' not in ctype:
            raise ValueError(f'Publisher returned non-HTML content ({ctype or "unknown content type"})')
        data = bytearray()
        for chunk in response.iter_content(65536):
            data.extend(chunk)
            if len(data) > max_bytes:
                raise ValueError('Publisher page exceeds the configured extraction size limit')
    finally:
        response.close()

    html = bytes(data).decode('utf-8', errors='replace')
    extracted = ''
    # Trafilatura's precision mode avoids much of the navigation and related-link clutter.
    try:
        import trafilatura
        candidate = trafilatura.extract(
            html, include_comments=False, include_tables=False,
            favor_precision=True, deduplicate=True,
        )
        if candidate and _usable_article_text(candidate):
            extracted = _normalise(candidate)
    except Exception:
        pass

    if not extracted:
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup(['script', 'style', 'noscript', 'nav', 'footer', 'header', 'aside', 'form', 'button', 'svg']):
            tag.decompose()
        for selector in ('[role="navigation"]', '[role="banner"]', '[role="contentinfo"]', '.nav', '.navbar', '.menu', '.sidebar', '.footer', '.header', '.newsletter', '.subscribe', '.sitemap', '.cookie', '.advertisement', '.related'):
            for node in soup.select(selector):
                node.decompose()
        container = soup.find('article') or soup.find('main')
        if container is not None:
            paragraphs = container.find_all(['p', 'h2', 'h3'])
        else:
            paragraphs = soup.find_all('p')
        parts = []
        for node in paragraphs:
            value = _normalise(node.get_text(' ', strip=True))
            if len(value.split()) >= 8 and not _is_boilerplate(value):
                parts.append(value)
        candidate = _normalise(' '.join(parts))
        if _usable_article_text(candidate):
            extracted = candidate

    if not extracted:
        raise ValueError('Publisher page loaded, but no reliable article body was found. It may be a sitemap, navigation page, paywall or JavaScript-only page.')
    return extracted[:100000]
