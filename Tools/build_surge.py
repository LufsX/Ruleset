import os
import datetime


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
        content_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                content_lines.append(line)

        rule_name = filename.replace(".conf", "")
        update_info = f"""#####################
# {rule_name}
# Last Updated: {(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%S") + "+08:00"}
#
# Form:
#  - https://ruleset.isteed.cc/List/Source/{rule_name}.conf
#####################
"""

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
