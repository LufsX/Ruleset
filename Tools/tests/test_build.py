import sys
from pathlib import Path
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build


class BuildPublishingTests(unittest.TestCase):
    def test_registry_loads_explicit_manifest(self):
        registry = build.create_registry()
        names = set(registry.task_ids())

        self.assertTrue(
            {
                "source.dnsmasq",
                "source.china-ip",
                "source.china-ipv6",
                "source.guard",
                "source.bankhk",
                "format.clash",
                "format.surge",
                "format.singbox",
                "format.smartdns",
                "format.mihomo",
                "page.markdown",
                "page.index",
            }
            <= names
        )
        self.assertEqual(
            set(registry.plugin_ids()),
            {
                "core",
                "bankhk",
                "china-ip",
                "china-ipv6",
                "dnsmasq",
                "guard",
                "clash",
                "mihomo",
                "singbox",
                "smartdns",
                "surge",
                "web",
            },
        )

    def test_build_lock_rejects_concurrent_build(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)

            with build.build_lock(project):
                with self.assertRaisesRegex(RuntimeError, "already running"):
                    with build.build_lock(project):
                        self.fail("the second lock should not be acquired")

    def test_publish_replaces_output_and_removes_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            staging = root / "staging"
            final = root / "Public"
            backup = root / "backup"
            staging.mkdir()
            final.mkdir()
            (staging / "version").write_text("new", encoding="utf-8")
            (final / "version").write_text("old", encoding="utf-8")

            build.publish_output(staging, final, backup)

            self.assertEqual((final / "version").read_text(encoding="utf-8"), "new")
            self.assertFalse(staging.exists())
            self.assertFalse(backup.exists())


if __name__ == "__main__":
    unittest.main()
