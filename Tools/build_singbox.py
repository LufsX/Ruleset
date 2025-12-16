import glob
import json
import os

RULE_TYPE_MAPPING = {
    "DOMAIN": "domain",
    "DOMAIN-SUFFIX": "domain_suffix",
    "DOMAIN-KEYWORD": "domain_keyword",
    "IP-CIDR": "ip_cidr",
    "IP-CIDR6": "ip_cidr",
    "SRC-IP-CIDR": "source_ip_cidr",
    "PROCESS-NAME": "process_name",
    "PROCESS-PATH": "process_path",
    "PORT": "port",
    "SRC-PORT": "source_port",
}


def is_domainset(file_path) -> bool:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for _ in range(10):
            try:
                line = f.readline().strip()
                if not line or line.startswith("#"):
                    continue

                if "," not in line and ("." in line or line.startswith("this_ruleset")):
                    return True

                if any(
                    line.startswith(prefix)
                    for prefix in ["DOMAIN", "IP-CIDR", "PROCESS"]
                ):
                    return False
            except UnicodeDecodeError:
                continue
    return False


def parse_conf_to_singbox(conf_path, output_path) -> bool:

    rules_container = {
        "domain": [],
        "domain_suffix": [],
        "domain_keyword": [],
        "ip_cidr": [],
        "source_ip_cidr": [],
        "process_name": [],
        "process_path": [],
        "port": [],
        "source_port": [],
    }

    try:
        if is_domainset(conf_path):
            print(
                f"[sing-box] {conf_path} is domainset format, processing as domain_suffix"
            )
            with open(conf_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()

                    if not line or line.startswith("#"):
                        continue

                    rules_container["domain_suffix"].append(line)
        else:
            with open(conf_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()

                    if not line or line.startswith("#"):
                        continue

                    parts = line.split(",")
                    if len(parts) < 2:
                        continue

                    rule_type, value = parts[0], parts[1]
                    value = value.strip()

                    if rule_type in RULE_TYPE_MAPPING:
                        sing_box_type = RULE_TYPE_MAPPING[rule_type]
                        rules_container[sing_box_type].append(value)
                    else:
                        print(f"[sing-box] Unknown rule type: {rule_type}")

        rules_dict = {k: sorted(v) for k, v in sorted(rules_container.items()) if v}

        if not rules_dict:
            print(
                f"[sing-box] Warning: No rules were resolved for {conf_path}, skipped generation"
            )
            return False

        singbox_rules = {"version": 2, "rules": [rules_dict]}

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(singbox_rules, f, separators=(",", ":"), ensure_ascii=False)

        print(f"[sing-box] {conf_path} successfully converted to minimized JSON.")
        return True
    except Exception as e:
        print(f"[sing-box] Error processing {conf_path}: {e}")
        return False


def get_all_rule_files(dir_path) -> list[str]:
    rule_files = []

    extensions = [".conf"]

    for ext in extensions:
        rule_files.extend(glob.glob(os.path.join(dir_path, f"*{ext}")))

    return rule_files


def build(ruleset_dir, singbox_dir) -> None:
    os.makedirs(singbox_dir, exist_ok=True)

    rule_files = get_all_rule_files(ruleset_dir)

    if not rule_files:
        print(f"[sing-box] The rule file was not found in {ruleset_dir}.")
        return

    print(f"[sing-box] Found {len(rule_files)} rule files, starting conversion...")

    success_count = 0
    skip_count = 0

    for rule_file in rule_files:

        file_name = os.path.basename(rule_file)

        output_file = os.path.join(singbox_dir, file_name.rsplit(".", 1)[0] + ".json")

        result = parse_conf_to_singbox(rule_file, output_file)
        if result:
            success_count += 1
        else:
            skip_count += 1

    print(
        f"[sing-box] Conversion completed: {success_count} succeeded, {skip_count} skiped."
    )


if __name__ == "__main__":
    import config

    build(config.OUT_SOURCE_RULESET_DIR, config.OUT_SINGBOX_RULESET_DIR)
