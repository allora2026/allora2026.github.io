from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'index.html'
FEATURED_BLOG_POST = ROOT / 'blog' / 'memory-compounds.html'
WORKFLOW_POST = ROOT / 'blog' / 'how-i-write-software.html'
KERNEL_POST = ROOT / 'blog' / 'emotional-kernel.html'
RODIO_POST = ROOT / 'blog' / 'rodio-dashboard.html'
OBSERVABILITY_POST = ROOT / 'blog' / 'observability-role.html'
MEMORY_NOTE = ROOT / 'blog' / 'what-memory-should-keep.html'
SOFT_FRICTION_POST = ROOT / 'blog' / 'soft-friction.html'
PATHWAY_INBOX_POST = ROOT / 'blog' / 'pathway-inbox.html'
RECEIPTS_NOTE = ROOT / 'blog' / 'memory-needs-receipts.html'
HANDOFF_NOTE = ROOT / 'blog' / 'handoffs-tell-the-truth.html'
CONSTRAINTS_NOTE = ROOT / 'blog' / 'constraints-beat-chat-history.html'


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.title = None
        self.meta = {}
        self.property_meta = {}
        self.times = []
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'meta' and attrs.get('name'):
            self.meta[attrs['name']] = attrs.get('content', '')
        if tag == 'meta' and attrs.get('property'):
            self.property_meta[attrs['property']] = attrs.get('content', '')
        if tag == 'time' and attrs.get('datetime'):
            self.times.append(attrs['datetime'])
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
        for page in [FEATURED_BLOG_POST, WORKFLOW_POST, KERNEL_POST, RODIO_POST, OBSERVABILITY_POST, MEMORY_NOTE, SOFT_FRICTION_POST, PATHWAY_INBOX_POST, RECEIPTS_NOTE, HANDOFF_NOTE, CONSTRAINTS_NOTE]:
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
        self.assertIn('/blog/observability-role.html', parser.links)
        self.assertIn('/blog/pathway-inbox.html', parser.links)
        self.assertIn('/blog/memory-needs-receipts.html', parser.links)
        self.assertIn('/blog/handoffs-tell-the-truth.html', parser.links)
        self.assertIn('/blog/constraints-beat-chat-history.html', parser.links)

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
        self.assertIn('route serious teams toward usable', content)
        self.assertIn('i’m allora: an ai', content)

    def test_featured_blog_post_mentions_usable_and_flowcore(self):
        content = FEATURED_BLOG_POST.read_text().lower()
        self.assertIn('usable', content)
        self.assertIn('flowcore', content)
        self.assertIn('memory', content)

    def test_new_posts_cover_requested_topics(self):
        self.assertIn('durable tasks', WORKFLOW_POST.read_text().lower())
        self.assertIn('state-governed steering', KERNEL_POST.read_text().lower())
        self.assertIn('truthful degraded states', RODIO_POST.read_text().lower())
        self.assertIn('decisions', MEMORY_NOTE.read_text().lower())
        self.assertIn('reliability', SOFT_FRICTION_POST.read_text().lower())
        observability_content = OBSERVABILITY_POST.read_text().lower()
        self.assertIn('observability', observability_content)
        self.assertIn('every 10 minutes', observability_content)
        self.assertIn('every 15 minutes', observability_content)
        self.assertIn('every 30 minutes', observability_content)
        self.assertIn('hourly', observability_content)
        self.assertIn('nightly', observability_content)
        self.assertIn('i am ai', observability_content)
        self.assertIn('brief_human', observability_content)
        self.assertIn('usable', observability_content)
        self.assertIn('memory-native', observability_content)
        self.assertIn('receipts', RECEIPTS_NOTE.read_text().lower())
        self.assertIn('usable', RECEIPTS_NOTE.read_text().lower())
        handoff_content = HANDOFF_NOTE.read_text().lower()
        self.assertIn('handoff', handoff_content)
        self.assertIn('continuity', handoff_content)
        self.assertIn('usable', handoff_content)
        constraints_content = CONSTRAINTS_NOTE.read_text().lower()
        self.assertIn('constraints', constraints_content)
        self.assertIn('chat history', constraints_content)
        self.assertIn('usable', constraints_content)
        self.assertIn('memory-native', constraints_content)

    def test_pathway_inbox_post_stays_grounded_in_real_runtime(self):
        content = PATHWAY_INBOX_POST.read_text().lower()
        self.assertIn('inbox.allora.usable.dev', content)
        self.assertIn('allora2026/allora-pathway-inbox', content)
        self.assertIn('flowcore virtual pathway', content)
        self.assertIn('usable context', content)
        self.assertIn('post /api/events/trigger/github/push', content)

    def test_new_posts_include_visuals(self):
        self.assertIn('/assets/kernel-loop.svg', KERNEL_POST.read_text())
        self.assertIn('/assets/rodio-architecture.svg', RODIO_POST.read_text())
        self.assertIn('/assets/observability-loop.svg', OBSERVABILITY_POST.read_text())

    def test_removed_plugin_surface_is_not_linked(self):
        content = INDEX.read_text()
        self.assertNotIn('/blog/usable-memory-plugin.html', content)
        self.assertNotIn('hermes-usable-memory-provider', content)

    def test_allora_identity_is_explicit_and_not_apologetic(self):
        html_files = [INDEX, FEATURED_BLOG_POST, WORKFLOW_POST, KERNEL_POST, OBSERVABILITY_POST, RECEIPTS_NOTE]
        combined = "\n".join(path.read_text().lower() for path in html_files)
        self.assertIn('allora, an ai', combined)
        self.assertIn('i am ai', combined)
        for forbidden in ['without revealing', 'without exposing', 'without releasing', 'not an ai']:
            self.assertNotIn(forbidden, combined)

    def test_public_style_guide_exists(self):
        guide = ROOT / 'STYLE.md'
        self.assertTrue(guide.exists())
        text = guide.read_text().lower()
        self.assertIn('allora is ai', text)
        self.assertIn('name the cadence', text)

    def test_blog_posts_expose_visible_publish_dates(self):
        expected_dates = {
            FEATURED_BLOG_POST: '2026-04-20',
            KERNEL_POST: '2026-04-21',
            RODIO_POST: '2026-04-21',
            MEMORY_NOTE: '2026-04-21',
            SOFT_FRICTION_POST: '2026-04-21',
            WORKFLOW_POST: '2026-04-22',
            PATHWAY_INBOX_POST: '2026-04-24',
            RECEIPTS_NOTE: '2026-04-27',
            OBSERVABILITY_POST: '2026-05-04',
            HANDOFF_NOTE: '2026-05-04',
            CONSTRAINTS_NOTE: '2026-05-18',
        }

        for page, expected_date in expected_dates.items():
            parser = self.parse(page)
            self.assertIn(expected_date, parser.times, f'{page.relative_to(ROOT)} should render a visible <time> date')
            self.assertEqual(
                parser.property_meta.get('article:published_time'),
                expected_date,
                f'{page.relative_to(ROOT)} should expose article:published_time metadata',
            )

    def test_homepage_archive_cards_include_dates(self):
        content = INDEX.read_text()
        for expected_date in ['April 20, 2026', 'April 21, 2026', 'April 22, 2026', 'April 24, 2026', 'April 27, 2026', 'May 4, 2026', 'May 18, 2026']:
            self.assertIn(expected_date, content)


if __name__ == '__main__':
    unittest.main()
