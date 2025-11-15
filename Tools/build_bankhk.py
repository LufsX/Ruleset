import datetime
import os


def build(bankhk_sources, ruleset_dir, out_ruleset_dir) -> None:
    print("[BankHK] Start building BankHK rules...")

    update_info = f'''#####################
# BankHK Ruleset
# Last Updated: {(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%S") + "+08:00"}
#
# Build form:
{'\n'.join([f"#  - {source}" for source in bankhk_sources])}
#####################

'''

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
    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(update_info)
        f.write("\n".join(all_rules))

    print(f"[BankHK] Successfully built BankHK.conf with {len(all_rules)} rules")
    print("[BankHK] End building BankHK rules")


if __name__ == "__main__":
    import config

    build(config.BANKHK_SOURCES, config.RULESET_DIR, config.OUT_SOURCE_RULESET_DIR)
