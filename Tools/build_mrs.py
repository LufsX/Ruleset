import os
import subprocess
import tempfile
import until


def _looks_like_cidr(s: str) -> bool:
    return "/" in s and any(c.isdigit() for c in s)


def _parse_value_after_type(line: str) -> str | None:
    if "," not in line:
        return None
    _, rest = line.split(",", 1)
    return rest.split(",", 1)[0].strip()


def _detect_convert_kind(clean_lines: list[str]) -> str | None:
    """返回 'domain' / 'ipcidr' / None(不可转换)"""
    if not clean_lines:
        return None

    has_comma = any("," in line for line in clean_lines)
    if not has_comma:
        # domainset / ipcidr 纯文本
        if all(_looks_like_cidr(line) for line in clean_lines):
            return "ipcidr"
        return "domain"

    # 逗号分隔规则（如 Surge/Clash 常见格式）
    allowed_domain_prefixes = ("DOMAIN,", "DOMAIN-SUFFIX,")
    allowed_ip_prefixes = ("IP-CIDR,", "IP-CIDR6,")

    if all(line.startswith(allowed_domain_prefixes) for line in clean_lines):
        return "domain"
    if all(line.startswith(allowed_ip_prefixes) for line in clean_lines):
        return "ipcidr"
    return None


def _normalize_for_domain(clean_lines: list[str]) -> list[str]:
    """把 domainset / DOMAIN / DOMAIN-SUFFIX 统一成 mihomo domain(text) 需要的格式。"""
    out: list[str] = []
    for line in clean_lines:
        if "," not in line:
            # domainset: '.example.com' -> '+.example.com'
            out.append(f"+{line}" if line.startswith(".") else line)
            continue

        if line.startswith("DOMAIN,"):
            value = _parse_value_after_type(line)
            if value:
                out.append(value)
            continue

        if line.startswith("DOMAIN-SUFFIX,"):
            value = _parse_value_after_type(line)
            if value:
                out.append(f"+.{value}")
            continue

        # 其他类型不应该进入这里
        raise ValueError(f"unsupported domain rule: {line}")
    return out


def _normalize_for_ipcidr(clean_lines: list[str]) -> list[str]:
    """把 ipcidr / IP-CIDR / IP-CIDR6 统一成 mihomo ipcidr(text) 需要的格式。"""
    out: list[str] = []
    for line in clean_lines:
        if "," not in line:
            out.append(line)
            continue

        if line.startswith(("IP-CIDR,", "IP-CIDR6,")):
            value = _parse_value_after_type(line)
            if value:
                out.append(value)
            continue

        raise ValueError(f"unsupported ipcidr rule: {line}")
    return out


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
    conf_files = [f for f in os.listdir(ruleset_dir) if f.endswith(".conf")]

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

        kind = _detect_convert_kind(clean_lines)
        if kind is None:
            copy_count += 1
            print(f"[mihomo] ✓ Processed non-convertible: {filename} -> .conf")
            continue

        # 生成 .mrs
        output_path = os.path.join(mihomo_dir, filename.rsplit(".", 1)[0] + ".mrs")

        try:
            normalized = (
                _normalize_for_domain(clean_lines)
                if kind == "domain"
                else _normalize_for_ipcidr(clean_lines)
            )
        except Exception as e:
            skip_count += 1
            print(f"[mihomo] Skip {filename}: {e}")
            continue

        normalized_sorted = sorted(normalized)

        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False, suffix=".txt"
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
    print("[mihomo] End processing ruleset files for mihomo")


if __name__ == "__main__":
    import config

    build(config.OUT_SOURCE_RULESET_DIR, config.OUT_MIHOMO_RULESET_DIR)
