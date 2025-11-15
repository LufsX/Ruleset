import os
import datetime


def build(smartdns_files, ruleset_dir) -> None:
    print("[SmartDNS] Start building smartdns rules...")

    # 确保目标目录存在
    smartdns_dir = os.path.join(ruleset_dir)
    if not os.path.exists(smartdns_dir):
        os.makedirs(smartdns_dir)

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
        header_lines = []
        for line in lines:
            if line.strip().startswith("#"):
                header_lines.append(line)
            else:
                break

        if header_lines:
            update_info = "".join(header_lines)
        else:
            update_info = f"""#####################
# {rule_name}
# Last Updated: {(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%S") + "+08:00"}
#
# Form:
#  - https://ruleset.isteed.cc/List/Source/{rule_name}.conf
#####################
"""

        # 获取非注释内容
        content_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                if line.startswith("."):
                    line = line.replace(".", "", 1)
                content_lines.append(line)

        # 排序内容
        content_lines.sort()

        # 写入目标文件
        with open(output_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(update_info)
            f.write("\n".join(content_lines))
            f.write("\n")

        processed_count += 1

    print(f"[SmartDNS] Completed: {processed_count} files processed")
    print("[SmartDNS] End building smartdns rules")


if __name__ == "__main__":
    import config

    build(config.DNSMASQ_CHINA_LIST, config.OUT_SOURCE_RULESET_DIR)
