import json
import sys
from pathlib import Path
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build_clash
import build_singbox
import build_smartdns


class ConverterTests(unittest.TestCase):
    def test_clash_domainset_ignores_indented_comments(self):
        content = "  # comment\n.example.com\nexact.example\n"

        self.assertTrue(build_clash.is_domainset(content))
        self.assertEqual(
            build_clash.process_domainset(content),
            ["+.example.com", "exact.example"],
        )

    def test_singbox_plain_cidr_becomes_ip_cidr(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "IP.conf"
            output = Path(directory) / "IP.json"
            source.write_text("1.2.3.0/24\n", encoding="utf-8")

            build_singbox.parse_conf_to_singbox(str(source), str(output))

            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result["rules"], [{"ip_cidr": ["1.2.3.0/24"]}])

    def test_singbox_rejects_unknown_rule_types(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "Unknown.conf"
            output = Path(directory) / "Unknown.json"
            source.write_text("UNKNOWN,example.com\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Unknown rule type"):
                build_singbox.parse_conf_to_singbox(str(source), str(output))

    def test_smartdns_accepts_only_plain_domainsets(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "Domain.conf"
            output = Path(directory) / "Domain.txt"
            source.write_text(".example.com\n", encoding="utf-8")

            build_smartdns.build({str(source): str(output)})

            self.assertIn("example.com\n", output.read_text(encoding="utf-8"))

            source.write_text("DOMAIN-SUFFIX,example.com\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "plain domainset"):
                build_smartdns.build({str(source): str(output)})


if __name__ == "__main__":
    unittest.main()
