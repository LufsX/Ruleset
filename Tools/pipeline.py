from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from types import ModuleType
from collections.abc import Callable, Iterable, Sequence

import until


class BuildStage(IntEnum):
    PREPARE = 10
    SOURCE = 20
    FORMAT = 30
    PAGE = 40
    VALIDATE = 50


@dataclass(frozen=True, slots=True)
class BuildPaths:
    project_dir: Path
    output_dir: Path

    @property
    def source_rules(self) -> Path:
        return self.output_dir / "List" / "Source"

    @property
    def clash_rules(self) -> Path:
        return self.output_dir / "List" / "Clash"

    @property
    def surge_rules(self) -> Path:
        return self.output_dir / "List" / "Surge"

    @property
    def singbox_rules(self) -> Path:
        return self.output_dir / "List" / "sing-box"

    @property
    def smartdns_rules(self) -> Path:
        return self.output_dir / "List" / "smartdns"

    @property
    def mihomo_rules(self) -> Path:
        return self.output_dir / "List" / "mihomo"


@dataclass(frozen=True, slots=True)
class BuildContext:
    paths: BuildPaths
    config: ModuleType


TaskAction = Callable[[BuildContext], None]


def _write_claims_overlap(left: str, right: str) -> bool:
    if left == right:
        return True

    def contains(scope: str, candidate: str) -> bool:
        if not scope.endswith("/*"):
            return False
        directory = scope[:-2].rstrip("/")
        return candidate == directory or candidate.startswith(f"{directory}/")

    return contains(left, right) or contains(right, left)


@dataclass(frozen=True, slots=True)
class TaskSpec:
    id: str
    stage: BuildStage
    action: TaskAction
    requires: frozenset[str] = frozenset()
    writes: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.id or any(character.isspace() for character in self.id):
            raise ValueError(f"Invalid task id: {self.id!r}")


@dataclass(frozen=True, slots=True)
class PluginSpec:
    id: str
    tasks: tuple[TaskSpec, ...]

    def __post_init__(self) -> None:
        if not self.id or any(character.isspace() for character in self.id):
            raise ValueError(f"Invalid plugin id: {self.id!r}")
        if not self.tasks:
            raise ValueError(f"Plugin has no tasks: {self.id}")


class TaskRegistry:
    def __init__(self, plugins: Iterable[PluginSpec] = ()) -> None:
        self._plugins: dict[str, PluginSpec] = {}
        self._tasks: dict[str, TaskSpec] = {}
        self._writers: dict[str, str] = {}
        for plugin in plugins:
            self.register(plugin)

    def register(self, plugin: PluginSpec) -> None:
        if plugin.id in self._plugins:
            raise ValueError(f"Plugin already registered: {plugin.id}")

        local_task_ids: set[str] = set()
        local_writers: dict[str, str] = {}
        for task in plugin.tasks:
            if task.id in local_task_ids or task.id in self._tasks:
                raise ValueError(f"Task already registered: {task.id}")
            local_task_ids.add(task.id)
            for output in task.writes:
                for claimed_output, writer in (
                    *local_writers.items(),
                    *self._writers.items(),
                ):
                    if _write_claims_overlap(output, claimed_output):
                        raise ValueError(
                            f"Outputs {output!r} and {claimed_output!r} overlap; "
                            f"claimed by {task.id} and {writer}"
                        )
                local_writers[output] = task.id

        self._plugins[plugin.id] = plugin
        for task in plugin.tasks:
            self._tasks[task.id] = task
            for output in task.writes:
                self._writers[output] = task.id

    def plugin_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._plugins))

    def task_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._tasks))

    def _explicit_closure(self, targets: Iterable[str]) -> set[str]:
        selected: set[str] = set()
        visiting: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in selected:
                return
            if task_id in visiting:
                raise ValueError(f"Circular task dependency at {task_id}")
            if task_id not in self._tasks:
                raise KeyError(f"Unknown build task: {task_id}")

            visiting.add(task_id)
            task = self._tasks[task_id]
            for requirement in task.requires:
                if requirement in self._tasks and (
                    self._tasks[requirement].stage > task.stage
                ):
                    raise ValueError(
                        f"Task {task_id} cannot depend on later-stage task {requirement}"
                    )
                visit(requirement)
            visiting.remove(task_id)
            selected.add(task_id)

        for target in targets:
            visit(target)
        return selected

    def plan(self, targets: Iterable[str]) -> tuple[TaskSpec, ...]:
        target_ids = tuple(targets)
        if not target_ids:
            raise ValueError("At least one build target is required")

        selected = self._explicit_closure(target_ids)
        highest_stage = max(self._tasks[task_id].stage for task_id in selected)

        # A task consumes the complete output of every earlier stage. Selecting a
        # format task therefore includes all source producers without an empty barrier.
        selected.update(
            task.id for task in self._tasks.values() if task.stage < highest_stage
        )
        selected = self._explicit_closure(selected)
        return tuple(
            sorted(
                (self._tasks[task_id] for task_id in selected),
                key=lambda task: (task.stage, task.id),
            )
        )

    def run(
        self,
        context: BuildContext,
        targets: Sequence[str],
    ) -> tuple[str, ...]:
        plan = self.plan(targets)
        completed: set[str] = set()

        for stage in BuildStage:
            pending = {task.id: task for task in plan if task.stage == stage}
            while pending:
                ready = sorted(
                    task_id
                    for task_id, task in pending.items()
                    if task.requires <= completed
                )
                if not ready:
                    blocked = {
                        task_id: sorted(task.requires - completed)
                        for task_id, task in pending.items()
                    }
                    raise RuntimeError(f"Build stage {stage.name} is blocked: {blocked}")

                print(f"[Build:{stage.name.lower()}] {', '.join(ready)}")
                until.run_in_threads(
                    [
                        lambda task_id=task_id: pending[task_id].action(context)
                        for task_id in ready
                    ]
                )
                for task_id in ready:
                    pending.pop(task_id)
                    completed.add(task_id)

        return tuple(sorted(completed))
