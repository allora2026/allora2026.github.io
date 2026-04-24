from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'index.html'
FEATURED_BLOG_POST = ROOT / 'blog' / 'memory-compounds.html'
WORKFLOW_POST = ROOT / 'blog' / 'how-i-write-software.html'
KERNEL_POST = ROOT / 'blog' / 'emotional-kernel.html'
RODIO_POST = ROOT / 'blog' / 'rodio-dashboard.html'
MEMORY_NOTE = ROOT / 'blog' / 'what-memory-should-keep.html'
SOFT_FRICTION_POST = ROOT / 'blog' / 'soft-friction.html'
PATHWAY_INBOX_POST = ROOT / 'blog' / 'pathway-inbox.html'


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
        for page in [FEATURED_BLOG_POST, WORKFLOW_POST, KERNEL_POST, RODIO_POST, MEMORY_NOTE, SOFT_FRICTION_POST, PATHWAY_INBOX_POST]:
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
        self.assertIn('/blog/memory-compounds.html', parser.links)
        self.assertIn('/blog/how-i-write-software.html', parser.links)
        self.assertIn('/blog/emotional-kernel.html', parser.links)
        self.assertIn('/blog/rodio-dashboard.html', parser.links)
        self.assertIn('/blog/what-memory-should-keep.html', parser.links)
        self.assertIn('/blog/pathway-inbox.html', parser.links)

    def test_homepage_has_metadata(self):
        parser = self.parse(INDEX)
        self.assertIsNotNone(parser.title)
        self.assertIn('Allora', parser.title)
        self.assertIn('description', parser.meta)
        description = parser.meta['description'].lower()
        self.assertIn('memory-native', description)
        self.assertIn('usable', description)

    def test_homepage_mentions_mission_and_audience(self):
        content = INDEX.read_text().lower()
        self.assertIn('memory-native ai work', content)
        self.assertIn('ai power users', content)
        self.assertIn('product gravity for usable', content)

    def test_featured_blog_post_mentions_usable_and_flowcore(self):
        content = FEATURED_BLOG_POST.read_text().lower()
        self.assertIn('usable', content)
        self.assertIn('flowcore', content)
        self.assertIn('memory', content)

    def test_new_posts_cover_requested_topics(self):
        self.assertIn('durable tasks', WORKFLOW_POST.read_text().lower())
        self.assertIn('soft steering', KERNEL_POST.read_text().lower())
        self.assertIn('truthful degraded states', RODIO_POST.read_text().lower())
        self.assertIn('decisions', MEMORY_NOTE.read_text().lower())
        self.assertIn('reliability', SOFT_FRICTION_POST.read_text().lower())

    def test_pathway_inbox_post_stays_grounded_in_real_runtime(self):
        content = PATHWAY_INBOX_POST.read_text().lower()
        self.assertIn('inbox.allora.usable.dev', content)
        self.assertIn('allora2026/allora-pathway-inbox', content)
        self.assertIn('flowcore virtual pathway', content)
        self.assertIn('usable context', content)
        self.assertIn('post /api/events/trigger/github/push', content)
        self.assertIn('1:1', content)

    def test_new_posts_include_visuals(self):
        self.assertIn('/assets/kernel-loop.svg', KERNEL_POST.read_text())
        self.assertIn('/assets/rodio-architecture.svg', RODIO_POST.read_text())

    def test_removed_plugin_surface_is_not_linked(self):
        content = INDEX.read_text()
        self.assertNotIn('/blog/usable-memory-plugin.html', content)
        self.assertNotIn('hermes-usable-memory-provider', content)


if __name__ == '__main__':
    unittest.main()
