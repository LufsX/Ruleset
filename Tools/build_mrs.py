import os
from pipeline import BuildStage, PluginSpec, TaskSpec
import rules
import subprocess
import tempfile
import until


def convert_with_mihomo(input_file: str, output_file: str, rule_type: str) -> bool:
    """
    使用 mihomo convert-ruleset 命令转换规则
    rule_type: "domain" 或 "ipcidr"
    """
    try:
        cmd = [
            "mihomo",
            "convert-ruleset",
            rule_type,
            "text",
            input_file,
            output_file,
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[mihomo] Command failed: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print(f"[mihomo] Command timeout for {input_file}")
        return False
    except FileNotFoundError:
        print("[mihomo] Error: mihomo command not found. Please install mihomo first.")
        return False
    except Exception as e:
        print(f"[mihomo] Error converting {input_file}: {e}")
        return False


def build(ruleset_dir, mihomo_dir) -> None:
    """
    从 Source 文件夹转换规则到 mihomo 文件夹
    """
    print("[mihomo] Start processing ruleset files for mihomo...")

    # 确保输出目录存在
    os.makedirs(mihomo_dir, exist_ok=True)

    # 获取所有 .conf 文件
    conf_files = sorted(f for f in os.listdir(ruleset_dir) if f.endswith(".conf"))

    if not conf_files:
        print(f"[mihomo] No rule files found in {ruleset_dir}")
        return

    print(f"[mihomo] Found {len(conf_files)} rule files, starting conversion...")

    success_count = 0
    skip_count = 0
    copy_count = 0

    for filename in conf_files:
        source_path = os.path.join(ruleset_dir, filename)
        rule_name = filename.replace(".conf", "")

        # 先输出清洗后的 .conf（“原文件复制排序保留”）
        clean_lines = until.read_clean_lines(source_path)
        clean_lines_sorted = sorted(clean_lines)
        until.write_lines_with_header(
            os.path.join(mihomo_dir, filename),
            until.make_ruleset_header(rule_name),
            clean_lines_sorted,
            sort_lines=False,
        )

        parsed_rules = rules.parse_rule_lines(clean_lines)
        kind = rules.detect_convert_kind(parsed_rules)
        if kind is None:
            copy_count += 1
            print(f"[mihomo] ✓ Processed non-convertible: {filename} -> .conf")
            continue

        # 生成 .mrs
        output_path = os.path.join(mihomo_dir, filename.rsplit(".", 1)[0] + ".mrs")

        try:
            normalized = rules.normalize_for_mihomo(parsed_rules, kind)
        except Exception as e:
            skip_count += 1
            print(f"[mihomo] Skip {filename}: {e}")
            continue

        normalized_sorted = sorted(normalized)

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            delete=False,
            suffix=".txt",
        ) as tmp:
            tmp.write("\n".join(normalized_sorted))
            tmp.write("\n")
            tmp_path = tmp.name

        try:
            if convert_with_mihomo(tmp_path, output_path, kind):
                success_count += 1
                print(f"[mihomo] ✓ Converted: {filename} -> .mrs & .conf")
            else:
                skip_count += 1
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    print(
        f"[mihomo] Conversion completed: {success_count} converted, {copy_count} copied, {skip_count} skipped"
    )
    if skip_count:
        raise RuntimeError(f"mihomo failed to convert {skip_count} ruleset(s)")
    print("[mihomo] End processing ruleset files for mihomo")


def _run(context) -> None:
    build(
        os.fspath(context.paths.source_rules),
        os.fspath(context.paths.mihomo_rules),
    )


PLUGIN = PluginSpec(
    id="mihomo",
    tasks=(
        TaskSpec(
            id="format.mihomo",
            stage=BuildStage.FORMAT,
            action=_run,
            writes=frozenset({"List/mihomo/*"}),
        ),
    ),
)


if __name__ == "__main__":
    import config

    build(config.OUT_SOURCE_RULESET_DIR, config.OUT_MIHOMO_RULESET_DIR)
