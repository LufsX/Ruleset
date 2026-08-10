import os
from pipeline import BuildStage, PluginSpec, TaskSpec
import rules
import until


def build(smartdns_files) -> None:
    print("[SmartDNS] Start building smartdns rules...")

    processed_count = 0

    # 处理所有文件
    for input_file, output_file in smartdns_files.items():
        if not os.path.exists(input_file):
            print(f"[SmartDNS] Warning: {input_file} does not exist, skipping...")
            continue

        rule_name = os.path.basename(input_file).replace(".conf", "")
        print(f"[SmartDNS] Processing {rule_name}...")

        # 读取源文件内容
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 获取文件头部信息
        update_info = until.extract_leading_comment_header(lines) or until.make_ruleset_header(
            rule_name
        )

        # 获取非注释内容
        parsed_rules = rules.parse_rule_lines(lines)
        if not rules.is_domainset(parsed_rules):
            raise ValueError(f"SmartDNS source must be a plain domainset: {input_file}")
        content_lines = sorted(
            {rule.value.removeprefix(".") for rule in parsed_rules}
        )

        # 写入目标文件
        until.write_lines_with_header(output_file, update_info, content_lines)

        processed_count += 1

    print(f"[SmartDNS] Completed: {processed_count} files processed")
    print("[SmartDNS] End building smartdns rules")


def _run(context) -> None:
    smartdns_files = {
        os.fspath(context.paths.source_rules / f"{name}.conf"): os.fspath(
            context.paths.smartdns_rules / f"{name}.txt"
        )
        for name in ("Guard", "ChinaApple", "ChinaDomain", "ChinaGoogle")
    }
    build(smartdns_files)


PLUGIN = PluginSpec(
    id="smartdns",
    tasks=(
        TaskSpec(
            id="format.smartdns",
            stage=BuildStage.FORMAT,
            action=_run,
            writes=frozenset({"List/smartdns/*"}),
        ),
    ),
)


if __name__ == "__main__":
    import config

    build(config.SMARTDNS_FILE)
