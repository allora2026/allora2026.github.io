"""Every public HTML page, including future articles, must carry pinned UWA."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TRACKER = {
    'defer': None,
    'data-domain': 'allora2026.github.io',
    'src': 'https://web-analytics.usable.dev/js/v1.0.0/uwa.js',
    'integrity': 'sha384-N3dVUWCLArSsxOtVuEe2Du1YTUvRsuSpSWXVItMO7jnl7JQQ7M+2OuXY/mpccqtD',
    'crossorigin': 'anonymous',
}


class TrackerParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_head = False
        self.trackers = []

    def handle_starttag(self, tag, attrs):
        if tag == 'head':
            self.in_head = True
        if tag == 'script':
            attributes = dict(attrs)
            src = attributes.get('src') or ''
            if 'uwa.js' in src or 'web-analytics.usable.dev' in src:
                self.trackers.append((self.in_head, attributes))

    def handle_endtag(self, tag):
        if tag == 'head':
            self.in_head = False


class AnalyticsTests(unittest.TestCase):
    def test_every_public_html_page_has_exactly_one_pinned_tracker_in_head(self):
        # Discover recursively rather than maintaining an article allowlist so
        # new pages cannot silently miss analytics. Hidden tooling is not served.
        pages = sorted(path for path in ROOT.rglob('*.html')
                       if not any(part.startswith('.')
                                  for part in path.relative_to(ROOT).parts))
        self.assertTrue(pages)
        self.assertIn(ROOT / 'index.html', pages)
        self.assertIn(ROOT / '404.html', pages)
        for page in pages:
            with self.subTest(page=str(page.relative_to(ROOT))):
                parser = TrackerParser()
                parser.feed(page.read_text(encoding='utf-8'))
                self.assertEqual(parser.trackers, [(True, TRACKER)])


if __name__ == '__main__':
    unittest.main()
