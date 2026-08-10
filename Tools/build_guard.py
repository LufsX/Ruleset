import os

from pipeline import BuildStage, PluginSpec, TaskSpec
import until


def download_and_process(link, exclude) -> list[str]:
    print(f"[Guard] Downloading and processing {link} ...")

    # 替换不可见字符表
    trans_table = str.maketrans({"\u200b": None, "\u200c": None})

    lines = []
    for line in until.fetch_text(link).splitlines():
        line = line.translate(trans_table).split("#", 1)[0].strip()
        if line and line not in exclude:
            lines.append(line)
    return lines


def build(guard_sources, out_dir) -> None:
    print("[Guard] Start building from Guard sources…")

    update_info = until.make_build_header("Guard List", guard_sources)
    exclude = ("", "switch.cup.com.cn", ".amazonaws.com")
    include = ("msmp.abchina.com.cn",)
    download_functions = [
        lambda link=link: download_and_process(link, exclude)
        for link in guard_sources
    ]
    all_lines = set(include)
    for source_lines in until.run_in_threads(download_functions):
        all_lines.update(source_lines)

    output_path = os.path.join(out_dir, "Guard.conf")
    until.write_lines_with_header(output_path, update_info, sorted(all_lines))

    print(f"[Guard] End building from Guard sources, {len(all_lines)} lines")


def _run(context) -> None:
    build(
        context.config.GUARD_SOURCES,
        os.fspath(context.paths.source_rules),
    )


PLUGIN = PluginSpec(
    id="guard",
    tasks=(
        TaskSpec(
            id="source.guard",
            stage=BuildStage.SOURCE,
            action=_run,
            writes=frozenset({"List/Source/Guard.conf"}),
        ),
    ),
)


if __name__ == "__main__":
    import config

    build(config.GUARD_SOURCES, config.OUT_SOURCE_RULESET_DIR)
