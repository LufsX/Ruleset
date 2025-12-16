import os
import until


def build(out_ruleset_dir, out_surge_ruleset_dir) -> None:
    print("[Surge] Start copying surge rules...")

    # 确保目标目录存在
    if not os.path.exists(out_surge_ruleset_dir):
        os.makedirs(out_surge_ruleset_dir)

    # 获取所有 .conf 文件
    conf_files = [f for f in os.listdir(out_ruleset_dir) if f.endswith(".conf")]
    processed_count = 0

    # 处理文件
    for filename in conf_files:
        source_file = os.path.join(out_ruleset_dir, filename)
        dest_file = os.path.join(out_surge_ruleset_dir, filename)

        # 读取源文件内容
        with open(source_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 过滤掉注释行并获取非空行
        content_lines = [
            line.strip()
            for line in lines
            if line.strip() and not line.strip().startswith("#")
        ]

        rule_name = filename.replace(".conf", "")
        update_info = until.make_ruleset_header(rule_name)

        # 写入目标文件
        with open(dest_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(update_info)
            # content_lines.sort()
            f.write("\n".join(content_lines))
            f.write("\n")

        processed_count += 1
        print(f"[Surge] Processed {filename} to Surge ruleset directory")

    print(
        f"[Surge] Completed: {processed_count} files processed to Surge ruleset directory"
    )
    print("[Surge] End processing surge rules")


if __name__ == "__main__":
    import config

    build(config.OUT_SOURCE_RULESET_DIR, config.OUT_SURGE_RULESET_DIR)
