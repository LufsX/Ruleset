import os

from pipeline import BuildStage, PluginSpec, TaskSpec
import until


def build(bankhk_sources, ruleset_dir, out_ruleset_dir) -> None:
    print("[BankHK] Start building BankHK rules...")

    update_info = until.make_build_header("BankHK Ruleset", bankhk_sources) + "\n"

    all_rules = []

    # 合并所有源文件
    for source in bankhk_sources:
        source_path = os.path.join(ruleset_dir, source)
        if os.path.exists(source_path):
            with open(source_path, "r", encoding="utf-8") as f:
                content = f.read()
                # 去除每个文件中的空行(注释还是不删掉吧)
                lines = [
                    line
                    for line in content.split("\n")
                    if line # and not line.startswith("#")
                ]
                all_rules.extend(lines)
                print(f"[BankHK] Processed {source}")
        else:
            print(f"[BankHK] Warning: Source file {source} not found")

    # 去重
    all_rules = list(dict.fromkeys(all_rules))

    # 写入合并后的文件
    output_path = os.path.join(out_ruleset_dir, "BankHK.conf")
    until.write_lines_with_header(output_path, update_info, all_rules)

    print(f"[BankHK] Successfully built BankHK.conf with {len(all_rules)} rules")
    print("[BankHK] End building BankHK rules")


def _run(context) -> None:
    build(
        context.config.BANKHK_SOURCES,
        os.fspath(context.paths.project_dir / "List"),
        os.fspath(context.paths.source_rules),
    )


PLUGIN = PluginSpec(
    id="bankhk",
    tasks=(
        TaskSpec(
            id="source.bankhk",
            stage=BuildStage.SOURCE,
            action=_run,
            writes=frozenset({"List/Source/BankHK.conf"}),
        ),
    ),
)


if __name__ == "__main__":
    import config

    build(config.BANKHK_SOURCES, config.RULESET_DIR, config.OUT_SOURCE_RULESET_DIR)
