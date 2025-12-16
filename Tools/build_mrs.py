import os
import subprocess
import tempfile
import datetime


def is_domainset(file_path) -> bool:
    """判断是否为纯域名集合格式"""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for _ in range(10):
            try:
                line = f.readline().strip()
                if not line or line.startswith("#"):
                    continue

                # 如果没有逗号且包含点号或以 this_ruleset 开头,判定为 domainset
                if "," not in line and ("." in line or line.startswith("this_ruleset")):
                    return True

                # 如果包含规则类型前缀,则不是 domainset
                if any(
                    line.startswith(prefix)
                    for prefix in ["DOMAIN", "IP-CIDR", "PROCESS"]
                ):
                    return False
            except UnicodeDecodeError:
                continue
    return False


def is_ipcidr(file_path) -> bool:
    """判断是否为纯 IPCIDR 格式"""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        non_comment_lines = []
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                non_comment_lines.append(line)
                if len(non_comment_lines) >= 10:
                    break

        if not non_comment_lines:
            return False

        # 检查是否所有非注释行都是 IP-CIDR 或纯 IP CIDR 格式
        for line in non_comment_lines:
            # 如果有逗号,检查是否为 IP-CIDR 前缀
            if "," in line:
                if not line.startswith("IP-CIDR,") and not line.startswith("IP-CIDR6,"):
                    return False
            else:
                # 纯 IP CIDR 格式: 包含 / 和数字
                if "/" not in line or not any(c.isdigit() for c in line):
                    return False

    return True


def check_convertible_to_domainset(file_path) -> tuple[bool, list[str]]:
    """
    检查文件是否只包含 DOMAIN/DOMAIN-SUFFIX/DOMAIN-KEYWORD 规则
    返回: (是否可转换, 转换后的域名列表)
    """
    domains = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split(",")
            if len(parts) < 2:
                # 可能是纯域名格式
                if "." in line:
                    domains.append(line)
                continue

            rule_type = parts[0].strip()
            value = parts[1].strip()

            if rule_type == "DOMAIN":
                domains.append(value)
            elif rule_type == "DOMAIN-SUFFIX":
                # DOMAIN-SUFFIX 转换为 +.domain 格式
                domains.append(f"+.{value}")
            elif rule_type == "DOMAIN-KEYWORD":
                # DOMAIN-KEYWORD 不适合转换为 domainset,返回 False
                return False, []
            elif rule_type.startswith("IP-CIDR"):
                # 包含 IP-CIDR 规则,不能转换为 domainset
                return False, []
            else:
                # 包含其他类型的规则,不能转换
                return False, []

    return len(domains) > 0, domains


def check_convertible_to_ipcidr(file_path) -> tuple[bool, list[str]]:
    """
    检查文件是否只包含 IP-CIDR 规则
    返回: (是否可转换, 转换后的 CIDR 列表)
    """
    cidrs = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split(",")
            if len(parts) < 2:
                # 可能是纯 CIDR 格式
                if "/" in line:
                    cidrs.append(line)
                continue

            rule_type = parts[0].strip()
            value = parts[1].strip()

            if rule_type in ["IP-CIDR", "IP-CIDR6"]:
                cidrs.append(value)
            else:
                # 包含非 IP-CIDR 规则,不能转换
                return False, []

    return len(cidrs) > 0, cidrs


def add_file_header(output_file: str, rule_name: str) -> None:
    """在转换后的文件前添加文件头"""
    update_info = f"""#####################
# {rule_name}
# Last Updated: {(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%S") + "+08:00"}
#
# Form:
#  - https://ruleset.isteed.cc/List/Source/{rule_name}.conf
#####################
"""
    # 读取现有内容
    with open(output_file, "rb") as f:
        content = f.read()
    
    # 写入文件头 + 原内容
    with open(output_file, "wb") as f:
        f.write(update_info.encode("utf-8"))
        f.write(content)


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
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, check=True
        )
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
        output_path = os.path.join(mihomo_dir, filename.rsplit(".", 1)[0] + ".mrs")
        rule_name = filename.replace(".conf", "")

        # 1. 检查是否为纯 domainset 格式
        if is_domainset(source_path):
            print(f"[mihomo] Processing domainset file: {filename}")
            # 读取并排序内容
            with open(source_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
            lines.sort()
            
            # 保存排序后的 .conf 文件
            conf_path = os.path.join(mihomo_dir, filename)
            update_info = f"""#####################
# {rule_name}
# Last Updated: {(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%S") + "+08:00"}
#
# Form:
#  - https://ruleset.isteed.cc/List/Source/{rule_name}.conf
#####################
"""
            with open(conf_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(update_info)
                f.write("\n".join(lines))
                f.write("\n")
            
            # 创建临时文件用于转换
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", delete=False, suffix=".txt"
            ) as tmp:
                tmp.write("\n".join(lines))
                tmp_path = tmp.name
            
            try:
                if convert_with_mihomo(tmp_path, output_path, "domain"):
                    add_file_header(output_path, rule_name)
                    success_count += 1
                    print(f"[mihomo] ✓ Converted domainset: {filename} -> .mrs & .conf")
                else:
                    skip_count += 1
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            continue

        # 2. 检查是否为纯 IPCIDR 格式
        if is_ipcidr(source_path):
            print(f"[mihomo] Processing ipcidr file: {filename}")
            # 读取并排序内容
            with open(source_path, "r", encoding="utf-8") as f:
                lines = []
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    # 处理带前缀的格式
                    if "," in line:
                        parts = line.split(",", 1)
                        if len(parts) >= 2:
                            lines.append(parts[1].strip())
                    else:
                        lines.append(line)
            lines.sort()
            
            # 保存排序后的 .conf 文件
            conf_path = os.path.join(mihomo_dir, filename)
            update_info = f"""#####################
# {rule_name}
# Last Updated: {(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%S") + "+08:00"}
#
# Form:
#  - https://ruleset.isteed.cc/List/Source/{rule_name}.conf
#####################
"""
            with open(conf_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(update_info)
                f.write("\n".join(lines))
                f.write("\n")
            
            # 创建临时文件用于转换
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", delete=False, suffix=".txt"
            ) as tmp:
                tmp.write("\n".join(lines))
                tmp_path = tmp.name
            
            try:
                if convert_with_mihomo(tmp_path, output_path, "ipcidr"):
                    add_file_header(output_path, rule_name)
                    success_count += 1
                    print(f"[mihomo] ✓ Converted ipcidr: {filename} -> .mrs & .conf")
                else:
                    skip_count += 1
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            continue

        # 3. 检查是否可以转换为 domainset (只包含 DOMAIN/DOMAIN-SUFFIX)
        can_convert_domain, domains = check_convertible_to_domainset(source_path)
        if can_convert_domain:
            print(
                f"[mihomo] Converting mixed domain rules to domainset: {filename} ({len(domains)} domains)"
            )
            # 排序域名
            domains.sort()
            
            # 保存排序后的 .conf 文件
            conf_path = os.path.join(mihomo_dir, filename)
            update_info = f"""#####################
# {rule_name}
# Last Updated: {(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%S") + "+08:00"}
#
# Form:
#  - https://ruleset.isteed.cc/List/Source/{rule_name}.conf
#####################
"""
            with open(conf_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(update_info)
                f.write("\n".join(domains))
                f.write("\n")
            
            # 创建临时文件用于转换
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", delete=False, suffix=".txt"
            ) as tmp:
                tmp.write("\n".join(domains))
                tmp_path = tmp.name

            try:
                if convert_with_mihomo(tmp_path, output_path, "domain"):
                    add_file_header(output_path, rule_name)
                    success_count += 1
                    print(
                        f"[mihomo] ✓ Converted to domainset: {filename} -> .mrs & .conf"
                    )
                else:
                    skip_count += 1
            finally:
                # 删除临时文件
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            continue

        # 4. 检查是否可以转换为 ipcidr (只包含 IP-CIDR)
        can_convert_ip, cidrs = check_convertible_to_ipcidr(source_path)
        if can_convert_ip:
            print(
                f"[mihomo] Converting mixed IP rules to ipcidr: {filename} ({len(cidrs)} CIDRs)"
            )
            cidrs.sort()
            
            # 保存排序后的 .conf 文件
            conf_path = os.path.join(mihomo_dir, filename)
            update_info = f"""#####################
# {rule_name}
# Last Updated: {(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%S") + "+08:00"}
#
# Form:
#  - https://ruleset.isteed.cc/List/Source/{rule_name}.conf
#####################
"""
            with open(conf_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(update_info)
                f.write("\n".join(cidrs))
                f.write("\n")
            
            # 创建临时文件用于转换
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", delete=False, suffix=".txt"
            ) as tmp:
                tmp.write("\n".join(cidrs))
                tmp_path = tmp.name

            try:
                if convert_with_mihomo(tmp_path, output_path, "ipcidr"):
                    add_file_header(output_path, rule_name)
                    success_count += 1
                    print(
                        f"[mihomo] ✓ Converted to ipcidr: {filename} -> .mrs & .conf"
                    )
                else:
                    skip_count += 1
            finally:
                # 删除临时文件
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            continue

        # 5. 包含其他类型规则,处理后复制
        print(f"[mihomo] Processing non-convertible file: {filename}")
        dest_path = os.path.join(mihomo_dir, filename)
        
        # 读取文件内容,去除注释并排序
        with open(source_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
        lines.sort()
        
        # 写入文件头和内容
        update_info = f"""#####################
# {rule_name}
# Last Updated: {(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%S") + "+08:00"}
#
# Form:
#  - https://ruleset.isteed.cc/List/Source/{rule_name}.conf
#####################
"""
        with open(dest_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(update_info)
            f.write("\n".join(lines))
            f.write("\n")
        
        copy_count += 1
        print(f"[mihomo] ✓ Processed: {filename}")

    print(
        f"[mihomo] Conversion completed: {success_count} converted, {copy_count} copied, {skip_count} skipped"
    )
    print("[mihomo] End processing ruleset files for mihomo")


if __name__ == "__main__":
    import config

    build(config.OUT_SOURCE_RULESET_DIR, config.OUT_MIHOMO_RULESET_DIR)
