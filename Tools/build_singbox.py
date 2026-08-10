import glob
import json
import os
from pipeline import BuildStage, PluginSpec, TaskSpec
import rules
import until

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
    return rules.is_domainset(rules.read_rules(file_path))


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

    parsed_rules = rules.read_rules(conf_path)
    if not parsed_rules:
        raise ValueError(f"No rules were resolved for {conf_path}")

    if all(rule.is_plain for rule in parsed_rules):
        kind = rules.detect_convert_kind(parsed_rules)
        if kind is None:
            raise ValueError(f"Mixed plain domain and CIDR entries in {conf_path}")
        key = "domain_suffix" if kind == "domain" else "ip_cidr"
        rules_container[key].extend(rule.value for rule in parsed_rules)
    else:
        if any(rule.is_plain for rule in parsed_rules):
            raise ValueError(f"Mixed plain and typed rules in {conf_path}")
        for rule in parsed_rules:
            if rule.type not in RULE_TYPE_MAPPING:
                raise ValueError(f"Unknown rule type {rule.type} in {conf_path}")
            rules_container[RULE_TYPE_MAPPING[rule.type]].append(rule.value)

    rules_dict = {
        key: sorted(set(values))
        for key, values in sorted(rules_container.items())
        if values
    }
    singbox_rules = {"version": 2, "rules": [rules_dict]}
    serialized = json.dumps(singbox_rules, separators=(",", ":"), ensure_ascii=False)
    until.write_text_atomic(output_path, serialized)

    print(f"[sing-box] {conf_path} successfully converted to minimized JSON.")
    return True


def get_all_rule_files(dir_path) -> list[str]:
    rule_files = []

    extensions = [".conf"]

    for ext in extensions:
        rule_files.extend(glob.glob(os.path.join(dir_path, f"*{ext}")))

    return sorted(rule_files)


def build(ruleset_dir, singbox_dir) -> None:
    os.makedirs(singbox_dir, exist_ok=True)

    rule_files = get_all_rule_files(ruleset_dir)

    if not rule_files:
        print(f"[sing-box] The rule file was not found in {ruleset_dir}.")
        return

    print(f"[sing-box] Found {len(rule_files)} rule files, starting conversion...")

    success_count = 0
    for rule_file in rule_files:

        file_name = os.path.basename(rule_file)

        output_file = os.path.join(singbox_dir, file_name.rsplit(".", 1)[0] + ".json")

        parse_conf_to_singbox(rule_file, output_file)
        success_count += 1

    print(f"[sing-box] Conversion completed: {success_count} succeeded.")


def _run(context) -> None:
    build(
        os.fspath(context.paths.source_rules),
        os.fspath(context.paths.singbox_rules),
    )


PLUGIN = PluginSpec(
    id="singbox",
    tasks=(
        TaskSpec(
            id="format.singbox",
            stage=BuildStage.FORMAT,
            action=_run,
            writes=frozenset({"List/sing-box/*"}),
        ),
    ),
)


if __name__ == "__main__":
    import config

    build(config.OUT_SOURCE_RULESET_DIR, config.OUT_SINGBOX_RULESET_DIR)
