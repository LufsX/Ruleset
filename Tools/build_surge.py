import os
from pipeline import BuildStage, PluginSpec, TaskSpec
import until


def build(out_ruleset_dir, out_surge_ruleset_dir) -> None:
    print("[Surge] Start copying surge rules...")

    # 确保目标目录存在
    os.makedirs(out_surge_ruleset_dir, exist_ok=True)

    # 获取所有 .conf 文件
    conf_files = sorted(f for f in os.listdir(out_ruleset_dir) if f.endswith(".conf"))
    processed_count = 0

    # 处理文件
    for filename in conf_files:
        source_file = os.path.join(out_ruleset_dir, filename)
        dest_file = os.path.join(out_surge_ruleset_dir, filename)

        # 读取源文件内容
        content_lines = until.read_clean_lines(source_file)

        rule_name = filename.replace(".conf", "")
        update_info = until.make_ruleset_header(rule_name)

        # 写入目标文件
        until.write_lines_with_header(dest_file, update_info, content_lines)

        processed_count += 1
        print(f"[Surge] Processed {filename} to Surge ruleset directory")

    print(
        f"[Surge] Completed: {processed_count} files processed to Surge ruleset directory"
    )
    print("[Surge] End processing surge rules")


def _run(context) -> None:
    build(
        os.fspath(context.paths.source_rules),
        os.fspath(context.paths.surge_rules),
    )


PLUGIN = PluginSpec(
    id="surge",
    tasks=(
        TaskSpec(
            id="format.surge",
            stage=BuildStage.FORMAT,
            action=_run,
            writes=frozenset({"List/Surge/*"}),
        ),
    ),
)


if __name__ == "__main__":
    import config

    build(config.OUT_SOURCE_RULESET_DIR, config.OUT_SURGE_RULESET_DIR)
