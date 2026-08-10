import os
from pipeline import BuildStage, PluginSpec, TaskSpec
import rules
import until


def is_domainset(content: str) -> bool:
    return rules.is_domainset(rules.parse_rule_text(content))


def process_domainset(content) -> list[str]:
    result = []

    for rule in rules.parse_rule_text(content):
        value = rule.value
        result.append(f"+{value}" if value.startswith(".") else value)

    return result


def process_non_domainset(content) -> list[str]:
    return [rule.to_line() for rule in rules.parse_rule_text(content)]


def build(out_ruleset_dir, out_clash_ruleset_dir) -> None:
    print("[Clash] Start processing ruleset files for Clash...")

    # 确保输出目录存在
    os.makedirs(out_clash_ruleset_dir, exist_ok=True)

    # 获取所有 .conf 文件
    conf_files = sorted(f for f in os.listdir(out_ruleset_dir) if f.endswith(".conf"))
    processed_count = 0

    for filename in conf_files:
        source_path = os.path.join(out_ruleset_dir, filename)
        dest_path = os.path.join(out_clash_ruleset_dir, filename)

        # 读取文件内容
        with open(source_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 创建文件头
        rule_name = filename.replace(".conf", "")
        update_info = until.make_ruleset_header(rule_name)
        domainset_flag = is_domainset(content)
        # 判断是否为 domainset 格式
        if domainset_flag:
            # 处理 domainset 格式
            processed_rules = process_domainset(content)
        else:
            # 处理非 domainset 格式
            processed_rules = process_non_domainset(content)

        # 写入处理后的内容
        until.write_lines_with_header(dest_path, update_info, processed_rules)

        print(f"[Clash] Processed{' domainset' if domainset_flag else ''} file: {filename}")
        processed_count += 1

    print(f"[Clash] Completed processing: {processed_count} files processed")
    print("[Clash] End processing ruleset files for Clash")


def _run(context) -> None:
    build(
        os.fspath(context.paths.source_rules),
        os.fspath(context.paths.clash_rules),
    )


PLUGIN = PluginSpec(
    id="clash",
    tasks=(
        TaskSpec(
            id="format.clash",
            stage=BuildStage.FORMAT,
            action=_run,
            writes=frozenset({"List/Clash/*"}),
        ),
    ),
)


if __name__ == "__main__":
    import config

    build(config.OUT_SOURCE_RULESET_DIR, config.OUT_CLASH_RULESET_DIR)
