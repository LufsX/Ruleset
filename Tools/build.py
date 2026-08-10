from __future__ import annotations

from contextlib import contextmanager
import datetime
import fcntl
import hashlib
import os
from pathlib import Path
import shutil
import tempfile
from collections.abc import Generator, Iterable

from build_manifest import DEFAULT_PLUGINS
import config
from pipeline import (
    BuildContext,
    BuildPaths,
    BuildStage,
    PluginSpec,
    TaskRegistry,
    TaskSpec,
)
import rules
import until


CONFIG_CLEAR_FILES = {
    "clash.yaml": "clash-nocomment.yaml",
    "surge.conf": "surge-nocomment.conf",
    "surge-autotest.conf": "surge-autotest-nocomment.conf",
    "mihomo.yaml": "mihomo-nocomment.yaml",
    "mihomo-smart.yaml": "mihomo-smart-nocomment.yaml",
}


def initialize(paths: BuildPaths) -> None:
    if paths.output_dir.exists():
        raise FileExistsError(f"Build directory already exists: {paths.output_dir}")
    for directory in (
        paths.source_rules,
        paths.clash_rules,
        paths.surge_rules,
        paths.singbox_rules,
        paths.smartdns_rules,
        paths.mihomo_rules,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def copy_static_files(paths: BuildPaths) -> None:
    print("[Build] Copy files that do not need to be generated...")
    for relative_path in config.COPY_PATH:
        source = paths.project_dir / relative_path
        destination = paths.output_dir / relative_path
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    shutil.copytree(
        paths.project_dir / "List",
        paths.source_rules,
        dirs_exist_ok=True,
    )
    shutil.copy2(paths.project_dir / "LICENSE", paths.output_dir / "LICENSE")

    source_readme = paths.source_rules / "README.md"
    destination_readme = paths.output_dir / "List" / "README.md"
    source_readme.replace(destination_readme)


def clear_config_comments(paths: BuildPaths) -> None:
    print("[Build] Start clearing config comments...")
    for source_name, destination_name in CONFIG_CLEAR_FILES.items():
        until.clear_comment(
            os.fspath(paths.output_dir / "Config" / source_name),
            os.fspath(paths.output_dir / "Config" / destination_name),
        )
    print("[Build] End clearing config comments")


def _stems(directory: Path, extension: str) -> set[str]:
    return {path.stem for path in directory.glob(f"*{extension}")}


def validate_output(paths: BuildPaths) -> None:
    source_names = _stems(paths.source_rules, ".conf")
    if not source_names:
        raise RuntimeError("No source rulesets were generated")

    expected_outputs = {
        "Clash": _stems(paths.clash_rules, ".conf"),
        "Surge": _stems(paths.surge_rules, ".conf"),
        "sing-box": _stems(paths.singbox_rules, ".json"),
        "mihomo": _stems(paths.mihomo_rules, ".conf"),
    }
    for name, output_names in expected_outputs.items():
        if output_names != source_names:
            missing = sorted(source_names - output_names)
            extra = sorted(output_names - source_names)
            raise RuntimeError(f"{name} output mismatch: missing={missing}, extra={extra}")

    expected_mrs = {
        path.stem
        for path in paths.source_rules.glob("*.conf")
        if rules.detect_convert_kind(rules.read_rules(os.fspath(path))) is not None
    }
    actual_mrs = _stems(paths.mihomo_rules, ".mrs")
    if actual_mrs != expected_mrs:
        raise RuntimeError(
            f"mihomo MRS output mismatch: missing={sorted(expected_mrs - actual_mrs)}, "
            f"extra={sorted(actual_mrs - expected_mrs)}"
        )

    expected_smartdns = {"Guard", "ChinaApple", "ChinaDomain", "ChinaGoogle"}
    actual_smartdns = _stems(paths.smartdns_rules, ".txt")
    if actual_smartdns != expected_smartdns:
        raise RuntimeError(
            f"SmartDNS output mismatch: missing={sorted(expected_smartdns - actual_smartdns)}, "
            f"extra={sorted(actual_smartdns - expected_smartdns)}"
        )

    for required_file in (paths.output_dir / "index.html", paths.output_dir / "LICENSE"):
        if not required_file.is_file() or required_file.stat().st_size == 0:
            raise RuntimeError(f"Required output is missing or empty: {required_file}")


def _prepare(context: BuildContext) -> None:
    initialize(context.paths)
    copy_static_files(context.paths)


def _clear_config(context: BuildContext) -> None:
    clear_config_comments(context.paths)


def _validate(context: BuildContext) -> None:
    validate_output(context.paths)


CORE_PLUGIN = PluginSpec(
    id="core",
    tasks=(
        TaskSpec(
            id="core.prepare",
            stage=BuildStage.PREPARE,
            action=_prepare,
            writes=frozenset({"workspace.static"}),
        ),
        TaskSpec(
            id="source.config",
            stage=BuildStage.SOURCE,
            action=_clear_config,
            writes=frozenset(
                f"Config/{name}" for name in CONFIG_CLEAR_FILES.values()
            ),
        ),
        TaskSpec(
            id="core.validate",
            stage=BuildStage.VALIDATE,
            action=_validate,
        ),
    ),
)


def create_registry(
    plugins: Iterable[PluginSpec] = DEFAULT_PLUGINS,
) -> TaskRegistry:
    return TaskRegistry((CORE_PLUGIN, *plugins))


def build_output(
    paths: BuildPaths, *, targets: tuple[str, ...] = ("core.validate",)
) -> tuple[str, ...]:
    registry = create_registry()
    context = BuildContext(paths=paths, config=config)
    return registry.run(context, targets)


def publish_output(staging_dir: Path, final_dir: Path, backup_dir: Path) -> None:
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    moved_existing = final_dir.exists()
    if moved_existing:
        final_dir.replace(backup_dir)
    try:
        staging_dir.replace(final_dir)
    except Exception:
        if moved_existing and backup_dir.exists() and not final_dir.exists():
            backup_dir.replace(final_dir)
        raise
    if backup_dir.exists():
        shutil.rmtree(backup_dir)


@contextmanager
def build_lock(project_dir: Path) -> Generator[None, None, None]:
    digest = hashlib.sha256(os.fspath(project_dir).encode()).hexdigest()[:16]
    lock_path = Path(tempfile.gettempdir()) / f"ruleset-build-{digest}.lock"
    with open(lock_path, "w", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError(
                f"Another build is already running for {project_dir}"
            ) from error
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def main() -> None:
    started_at = datetime.datetime.now()
    project_dir = Path(config.PROCESS_DIR)
    final_dir = Path(config.OUT_DIR)
    with build_lock(project_dir):
        temporary_root = Path(
            tempfile.mkdtemp(prefix=".ruleset-build-", dir=os.fspath(project_dir))
        )
        staging_dir = temporary_root / "Public"
        backup_dir = temporary_root / "previous-Public"
        try:
            build_output(BuildPaths(project_dir=project_dir, output_dir=staging_dir))
            publish_output(staging_dir, final_dir, backup_dir)
        finally:
            shutil.rmtree(temporary_root, ignore_errors=True)

    print(f"Total time: {datetime.datetime.now() - started_at}")


if __name__ == "__main__":
    main()
