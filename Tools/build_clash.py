import os
import until


def is_domainset(content) -> bool:
    lines = content.strip().split("\n")
    non_comment_lines = [line for line in lines if line and not line.startswith("#")]

    if not non_comment_lines:
        return False

    if any("," in line for line in non_comment_lines):
        return False
    return True


def process_domainset(content) -> list[str]:
    lines = content.split("\n")
    result = []

    for line in lines:
        if line.startswith("#") or not line.strip():
            continue
        # 如果以 . 开头，添加 + 前缀
        if line.startswith("."):
            result.append(f"+{line}")
        # 其他域名格式不变
        else:
            result.append(line)

    return result


def process_non_domainset(content) -> list[str]:
    lines = content.split("\n")
    result = []

    for line in lines:
        if not line.strip() or line.startswith("#"):
            continue
        result.append(line)

    return result


def build(out_ruleset_dir, out_clash_ruleset_dir) -> None:
    print("[Clash] Start processing ruleset files for Clash...")

    # 确保输出目录存在
    if not os.path.exists(out_clash_ruleset_dir):
        os.makedirs(out_clash_ruleset_dir)

    # 获取所有 .conf 文件
    conf_files = [f for f in os.listdir(out_ruleset_dir) if f.endswith(".conf")]
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
        with open(dest_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(update_info)
            # processed_rules.sort()
            f.write("\n".join(processed_rules))
            f.write("\n")

        print(f"[Clash] Processed{' domainset' if domainset_flag else ''} file: {filename}")
        processed_count += 1

    print(f"[Clash] Completed processing: {processed_count} files processed")
    print("[Clash] End processing ruleset files for Clash")


if __name__ == "__main__":
    import config

    build(config.OUT_SOURCE_RULESET_DIR, config.OUT_CLASH_RULESET_DIR)
