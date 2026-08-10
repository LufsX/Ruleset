import sys
from pathlib import Path
import tempfile
from types import ModuleType
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline import (
    BuildContext,
    BuildPaths,
    BuildStage,
    PluginSpec,
    TaskRegistry,
    TaskSpec,
)


def task(task_id, stage, action=lambda _context: None, **kwargs):
    return TaskSpec(id=task_id, stage=stage, action=action, **kwargs)


class PipelineTests(unittest.TestCase):
    def make_context(self, directory):
        return BuildContext(
            BuildPaths(Path(directory), Path(directory) / "output"),
            ModuleType("config"),
        )

    def test_format_target_includes_every_previous_stage(self):
        events = []
        registry = TaskRegistry(
            (
                PluginSpec(
                    "test",
                    (
                        task(
                            "prepare",
                            BuildStage.PREPARE,
                            lambda _context: events.append("prepare"),
                        ),
                        task(
                            "source.one",
                            BuildStage.SOURCE,
                            lambda _context: events.append("source.one"),
                        ),
                        task(
                            "source.two",
                            BuildStage.SOURCE,
                            lambda _context: events.append("source.two"),
                        ),
                        task(
                            "format.target",
                            BuildStage.FORMAT,
                            lambda _context: events.append("format.target"),
                        ),
                        task(
                            "format.unrelated",
                            BuildStage.FORMAT,
                            lambda _context: events.append("format.unrelated"),
                        ),
                    ),
                ),
            )
        )

        with tempfile.TemporaryDirectory() as directory:
            completed = registry.run(
                self.make_context(directory), ("format.target",)
            )

        self.assertEqual(events[0], "prepare")
        self.assertEqual(set(events[1:3]), {"source.one", "source.two"})
        self.assertEqual(events[3], "format.target")
        self.assertNotIn("format.unrelated", events)
        self.assertEqual(
            set(completed),
            {"prepare", "source.one", "source.two", "format.target"},
        )

    def test_source_target_does_not_include_peer_tasks(self):
        registry = TaskRegistry(
            (
                PluginSpec(
                    "test",
                    (
                        task("prepare", BuildStage.PREPARE),
                        task("source.target", BuildStage.SOURCE),
                        task("source.unrelated", BuildStage.SOURCE),
                    ),
                ),
            )
        )

        self.assertEqual(
            [item.id for item in registry.plan(("source.target",))],
            ["prepare", "source.target"],
        )

    def test_same_stage_dependencies_run_in_order(self):
        events = []
        registry = TaskRegistry(
            (
                PluginSpec(
                    "test",
                    (
                        task(
                            "page.markdown",
                            BuildStage.PAGE,
                            lambda _context: events.append("markdown"),
                        ),
                        task(
                            "page.index",
                            BuildStage.PAGE,
                            lambda _context: events.append("index"),
                            requires=frozenset({"page.markdown"}),
                        ),
                    ),
                ),
            )
        )

        with tempfile.TemporaryDirectory() as directory:
            registry.run(self.make_context(directory), ("page.index",))

        self.assertEqual(events, ["markdown", "index"])

    def test_rejects_unknown_dependencies(self):
        registry = TaskRegistry(
            (
                PluginSpec(
                    "test",
                    (
                        task(
                            "target",
                            BuildStage.SOURCE,
                            requires=frozenset({"missing"}),
                        ),
                    ),
                ),
            )
        )

        with self.assertRaisesRegex(KeyError, "missing"):
            registry.plan(("target",))

    def test_rejects_duplicate_outputs_within_plugin(self):
        plugin = PluginSpec(
            "test",
            (
                task(
                    "one",
                    BuildStage.SOURCE,
                    writes=frozenset({"same-output"}),
                ),
                task(
                    "two",
                    BuildStage.SOURCE,
                    writes=frozenset({"same-output"}),
                ),
            ),
        )

        with self.assertRaisesRegex(ValueError, "same-output"):
            TaskRegistry((plugin,))

    def test_rejects_file_inside_claimed_output_directory(self):
        directory_plugin = PluginSpec(
            "directory",
            (
                task(
                    "directory-writer",
                    BuildStage.FORMAT,
                    writes=frozenset({"List/Clash/*"}),
                ),
            ),
        )
        file_plugin = PluginSpec(
            "file",
            (
                task(
                    "file-writer",
                    BuildStage.FORMAT,
                    writes=frozenset({"List/Clash/example.conf"}),
                ),
            ),
        )

        registry = TaskRegistry((directory_plugin,))
        with self.assertRaisesRegex(ValueError, "overlap"):
            registry.register(file_plugin)


if __name__ == "__main__":
    unittest.main()
