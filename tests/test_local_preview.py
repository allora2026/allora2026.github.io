import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "local_preview.py"
REGISTRY_PATH = ROOT / "local_preview_registry.json"


def load_module():
    spec = importlib.util.spec_from_file_location("local_preview", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class LocalPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.local_preview = load_module()

    def write_registry(self, payload):
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        with handle:
            json.dump(payload, handle)
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        return Path(handle.name)

    def test_two_projects_get_different_assigned_ports(self):
        registry_path = self.write_registry(
            {
                "defaults": {
                    "localhost_host": "127.0.0.1",
                    "port_min": 41000,
                    "port_max": 41999,
                    "command_template": [
                        "python3",
                        "-m",
                        "http.server",
                        "{port}",
                        "--bind",
                        "{host}",
                        "--directory",
                        "{path}",
                    ],
                },
                "projects": {
                    "alpha-demo": {"path": "."},
                    "beta-demo": {"path": "."},
                },
            }
        )
        registry = self.local_preview.load_registry(registry_path)

        assigned = self.local_preview.materialize_project_ports(registry)

        self.assertIn("alpha-demo", assigned)
        self.assertIn("beta-demo", assigned)
        self.assertNotEqual(assigned["alpha-demo"], assigned["beta-demo"])
        self.assertEqual(
            assigned,
            self.local_preview.materialize_project_ports(
                self.local_preview.load_registry(registry_path)
            ),
        )

    def test_bind_rules_use_localhost_or_explicit_tailscale_only(self):
        self.assertEqual(self.local_preview.resolve_bind_host(None), "127.0.0.1")
        self.assertEqual(
            self.local_preview.resolve_bind_host("100.88.77.66"), "100.88.77.66"
        )
        with self.assertRaises(ValueError):
            self.local_preview.resolve_bind_host("0.0.0.0")

    def test_reported_urls_include_project_and_port(self):
        registry = self.local_preview.load_registry(REGISTRY_PATH)
        plan = self.local_preview.build_preview_plan(
            "allora2026-site",
            registry,
            tailscale_ip="100.88.77.66",
        )
        rendered = self.local_preview.render_preview_report(plan)

        self.assertIn("allora2026-site", rendered)
        self.assertIn(str(plan["port"]), rendered)
        self.assertIn(f"http://127.0.0.1:{plan['port']}/", rendered)
        self.assertIn(f"http://100.88.77.66:{plan['port']}/", rendered)

    def test_command_output_uses_safe_bind_host(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.local_preview.main(["command", "allora2026-site"])

        rendered = output.getvalue().strip()
        self.assertIn("--bind 127.0.0.1", rendered)
        self.assertNotIn("0.0.0.0", rendered)


if __name__ == "__main__":
    unittest.main()
