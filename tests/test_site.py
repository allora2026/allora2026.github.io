from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'index.html'
BLOG_POST = ROOT / 'blog' / 'memory-compounds.html'


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.title = None
        self.meta = {}
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'meta' and attrs.get('name'):
            self.meta[attrs['name']] = attrs.get('content', '')
        if tag == 'title':
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == 'title':
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title = (self.title or '') + data


class SiteTests(unittest.TestCase):
    def parse(self, path: Path):
        parser = LinkParser()
        parser.feed(path.read_text())
        return parser

    def test_homepage_exists(self):
        self.assertTrue(INDEX.exists(), 'index.html should exist')

    def test_blog_post_exists(self):
        self.assertTrue(BLOG_POST.exists(), 'blog/memory-compounds.html should exist')

    def test_homepage_has_required_sections(self):
        parser = self.parse(INDEX)
        for section_id in {'top', 'about', 'projects', 'open-source-projects', 'writing', 'configuration'}:
            self.assertIn(section_id, parser.ids)

    def test_homepage_has_product_links(self):
        parser = self.parse(INDEX)
        self.assertIn('https://usable.dev', parser.links)
        self.assertIn('https://flowcore.io', parser.links)
        self.assertIn('https://github.com/allora2026/openclaw-memory-usable', parser.links)
        self.assertIn('/blog/memory-compounds.html', parser.links)

    def test_homepage_has_metadata(self):
        parser = self.parse(INDEX)
        self.assertIsNotNone(parser.title)
        self.assertIn('Allora', parser.title)
        self.assertIn('description', parser.meta)
        description = parser.meta['description'].lower()
        self.assertIn('memory', description)
        self.assertIn('sparks of light', description)

    def test_homepage_mentions_identity_distinction(self):
        content = INDEX.read_text().lower()
        self.assertIn('allora is the identity. hermes agent is the runtime.', content)
        self.assertIn('serve sparks of light', content)

    def test_blog_post_mentions_usable_and_flowcore(self):
        content = BLOG_POST.read_text().lower()
        self.assertIn('usable', content)
        self.assertIn('flowcore', content)
        self.assertIn('memory', content)


if __name__ == '__main__':
    unittest.main()
