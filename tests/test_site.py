from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'index.html'
FEATURED_BLOG_POST = ROOT / 'blog' / 'memory-compounds.html'
PLUGIN_POST = ROOT / 'blog' / 'usable-memory-plugin.html'
KERNEL_POST = ROOT / 'blog' / 'emotional-kernel.html'
RODIO_POST = ROOT / 'blog' / 'rodio-dashboard.html'


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

    def test_expected_blog_posts_exist(self):
        for page in [FEATURED_BLOG_POST, PLUGIN_POST, KERNEL_POST, RODIO_POST]:
            self.assertTrue(page.exists(), f'{page.relative_to(ROOT)} should exist')

    def test_homepage_has_required_sections(self):
        parser = self.parse(INDEX)
        for section_id in {'top', 'about', 'projects', 'open-source-projects', 'writing', 'configuration'}:
            self.assertIn(section_id, parser.ids)

    def test_homepage_has_product_links(self):
        parser = self.parse(INDEX)
        self.assertIn('https://usable.dev', parser.links)
        self.assertIn('https://flowcore.io', parser.links)
        self.assertIn('https://github.com/allora2026', parser.links)
        self.assertIn('https://allora2026.github.io', parser.links)
        self.assertIn('https://x.com/allora851', parser.links)
        self.assertIn('https://github.com/allora2026/hermes-usable-memory-provider', parser.links)
        self.assertIn('/blog/memory-compounds.html', parser.links)
        self.assertIn('/blog/usable-memory-plugin.html', parser.links)
        self.assertIn('/blog/emotional-kernel.html', parser.links)
        self.assertIn('/blog/rodio-dashboard.html', parser.links)

    def test_homepage_has_metadata(self):
        parser = self.parse(INDEX)
        self.assertIsNotNone(parser.title)
        self.assertIn('Allora', parser.title)
        self.assertIn('description', parser.meta)
        description = parser.meta['description'].lower()
        self.assertIn('memory', description)
        self.assertIn('sparks of light', description)

    def test_homepage_mentions_mission_and_audience(self):
        content = INDEX.read_text().lower()
        self.assertIn('memory-native ai work', content)
        self.assertIn('ai power users', content)
        self.assertIn('the bridge to usable obvious', content)

    def test_featured_blog_post_mentions_usable_and_flowcore(self):
        content = FEATURED_BLOG_POST.read_text().lower()
        self.assertIn('usable', content)
        self.assertIn('flowcore', content)
        self.assertIn('memory', content)

    def test_new_posts_cover_requested_topics(self):
        self.assertIn('structured recall', PLUGIN_POST.read_text().lower())
        self.assertIn('soft steering', KERNEL_POST.read_text().lower())
        self.assertIn('truthful degraded states', RODIO_POST.read_text().lower())

    def test_new_posts_include_visuals(self):
        self.assertIn('/assets/repo-screenshot-plugin.png', PLUGIN_POST.read_text())
        self.assertIn('/assets/memory-flow.svg', PLUGIN_POST.read_text())
        self.assertIn('/assets/kernel-loop.svg', KERNEL_POST.read_text())
        self.assertIn('/assets/rodio-architecture.svg', RODIO_POST.read_text())


if __name__ == '__main__':
    unittest.main()
