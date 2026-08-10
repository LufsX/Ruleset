import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import rules


class RuleParsingTests(unittest.TestCase):
    def test_parse_typed_rule_preserves_options(self):
        rule = rules.parse_rule_line(" domain-suffix, example.com, no-resolve ")

        self.assertEqual(rule.type, "DOMAIN-SUFFIX")
        self.assertEqual(rule.value, "example.com")
        self.assertEqual(rule.options, ("no-resolve",))
        self.assertEqual(rule.to_line(), "DOMAIN-SUFFIX,example.com,no-resolve")

    def test_parse_skips_empty_and_indented_comments(self):
        parsed = rules.parse_rule_text("\n  # comment\n.example.com\n")

        self.assertEqual(parsed, [rules.Rule(None, ".example.com")])

    def test_detects_plain_cidr_without_treating_it_as_domainset(self):
        parsed = rules.parse_rule_text("1.2.3.0/24\n2001:db8::/32\n")

        self.assertEqual(rules.detect_convert_kind(parsed), "ipcidr")
        self.assertFalse(rules.is_domainset(parsed))

    def test_mixed_plain_entries_are_not_convertible(self):
        parsed = rules.parse_rule_text("example.com\n1.2.3.0/24\n")

        self.assertIsNone(rules.detect_convert_kind(parsed))

    def test_normalizes_mihomo_domain_rules(self):
        parsed = rules.parse_rule_text(
            "DOMAIN,exact.example\nDOMAIN-SUFFIX,suffix.example,no-resolve\n"
        )

        self.assertEqual(
            rules.normalize_for_mihomo(parsed, "domain"),
            ["exact.example", "+.suffix.example"],
        )


if __name__ == "__main__":
    unittest.main()
