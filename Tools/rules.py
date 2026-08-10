from __future__ import annotations

from dataclasses import dataclass
import ipaddress
from typing import Iterable, Literal


RuleKind = Literal["domain", "ipcidr"]

DOMAIN_RULE_TYPES = frozenset({"DOMAIN", "DOMAIN-SUFFIX"})
IP_RULE_TYPES = frozenset({"IP-CIDR", "IP-CIDR6"})


@dataclass(frozen=True, slots=True)
class Rule:
    """A normalized Surge-style rule or a plain domain/IP set entry."""

    type: str | None
    value: str
    options: tuple[str, ...] = ()

    @property
    def is_plain(self) -> bool:
        return self.type is None

    def to_line(self) -> str:
        if self.type is None:
            return self.value
        return ",".join((self.type, self.value, *self.options))


def parse_rule_line(line: str) -> Rule | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    parts = tuple(part.strip() for part in stripped.split(","))
    if len(parts) == 1:
        return Rule(type=None, value=parts[0])
    if not parts[0] or not parts[1]:
        raise ValueError(f"invalid rule: {line.rstrip()}")
    return Rule(type=parts[0].upper(), value=parts[1], options=parts[2:])


def parse_rule_lines(lines: Iterable[str]) -> list[Rule]:
    parsed: list[Rule] = []
    for line_number, line in enumerate(lines, start=1):
        try:
            rule = parse_rule_line(line)
        except ValueError as error:
            raise ValueError(f"line {line_number}: {error}") from error
        if rule is not None:
            parsed.append(rule)
    return parsed


def parse_rule_text(content: str) -> list[Rule]:
    return parse_rule_lines(content.splitlines())


def read_rules(file_path: str) -> list[Rule]:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        return parse_rule_lines(file)


def is_cidr(value: str) -> bool:
    try:
        ipaddress.ip_network(value, strict=False)
        return True
    except ValueError:
        return False


def detect_convert_kind(parsed_rules: Iterable[Rule]) -> RuleKind | None:
    items = list(parsed_rules)
    if not items:
        return None

    if all(rule.is_plain for rule in items):
        cidr_flags = [is_cidr(rule.value) for rule in items]
        if all(cidr_flags):
            return "ipcidr"
        if not any(cidr_flags):
            return "domain"
        return None

    if any(rule.is_plain for rule in items):
        return None

    rule_types = {rule.type for rule in items}
    if rule_types <= DOMAIN_RULE_TYPES:
        return "domain"
    if rule_types <= IP_RULE_TYPES:
        return "ipcidr"
    return None


def is_domainset(parsed_rules: Iterable[Rule]) -> bool:
    items = list(parsed_rules)
    return bool(items) and all(rule.is_plain for rule in items) and (
        detect_convert_kind(items) == "domain"
    )


def normalize_for_mihomo(parsed_rules: Iterable[Rule], kind: RuleKind) -> list[str]:
    normalized: list[str] = []
    for rule in parsed_rules:
        if rule.is_plain:
            value = rule.value
            if kind == "domain" and value.startswith("."):
                value = f"+{value}"
            normalized.append(value)
            continue

        if kind == "domain" and rule.type == "DOMAIN":
            normalized.append(rule.value)
        elif kind == "domain" and rule.type == "DOMAIN-SUFFIX":
            normalized.append(f"+.{rule.value}")
        elif kind == "ipcidr" and rule.type in IP_RULE_TYPES:
            normalized.append(rule.value)
        else:
            raise ValueError(f"unsupported {kind} rule: {rule.to_line()}")
    return normalized
