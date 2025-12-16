import os
import re
import requests

import until
from until import run_in_threads


def download_and_process(name, link, out_dir) -> None:
    print(f"[dnsmasq] Start download and process {name}")
    content = requests.get(link).text

    update_info = until.make_build_header(f"{name} List", [link])

    pattern = r"^server=/(.*)/114\.114\.114\.114$$"
    matches = [
        match
        for match in re.findall(pattern, content, re.MULTILINE)
        if not match.startswith("#")
    ]

    with open(os.path.join(out_dir, f"{name}.conf"), "w", newline="\n") as outfile:
        outfile.write(update_info)
        outfile.write("\n".join(matches))

    print(f"[dnsmasq] End downloading and processing {name}")


def build(dnsmasq_china_list, out_dir) -> None:
    print("[dnsmasq] Start building from dnsmasq china list…")

    download_functions = [
        lambda name=name, link=link: download_and_process(name, link, out_dir)
        for name, link in dnsmasq_china_list.items()
    ]

    run_in_threads(download_functions)

    print("[dnsmasq] End building from dnsmasq china list")


if __name__ == "__main__":
    import config
    build(config.DNSMASQ_CHINA_LIST, config.OUT_SOURCE_RULESET_DIR)
