import datetime
import ipaddress
import os
import requests

from until import run_in_threads


def download_and_process(link, exclude) -> list[str]:
    print(f"[ChinaIPv6] Downloading and processing {link} ...")
    content = requests.get(link).text
    lines = [
        line
        for line in content.split("\n")
        if line and not line.startswith("#") and line.strip() not in exclude
    ]
    return lines


def build(china_ipv6_sources, out_dir) -> None:
    print("[ChinaIPv6] Start building from China IPv6 sources…")

    update_info = f'''#####################
# China IPv6 List
# Last Updated: {(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%S") + "+08:00"}
#
# Build form:
{'\n'.join([f"#  - {link}" for link in china_ipv6_sources])}
#####################
'''
    exclude = {
        # Space
        "",
    }

    all_lines = set()

    def download_and_process_wrapper(link, exclude) -> None:
        lines = download_and_process(link, exclude)
        all_lines.update(lines)

    download_functions = [
        lambda link=link: download_and_process_wrapper(link, exclude)
        for link in china_ipv6_sources
    ]

    run_in_threads(download_functions)

    all_networks = set()

    for line in all_lines:
        try:
            network = ipaddress.ip_network(line.strip(), strict=False)
            all_networks.add(network)
        except ValueError:
            print(f"[ChinaIPv6] Invalid network format: {line}")

    merged_networks = ipaddress.collapse_addresses(all_networks)

    with open(os.path.join(out_dir, "ChinaIPv6.conf"), "w", newline="\n") as f:
        f.write(update_info)
        for network in merged_networks:
            f.write(f"IP-CIDR6,{network}\n")

    print("[ChinaIPv6] End building from china IPv6 sources")


if __name__ == "__main__":
    import config

    build(config.CHINA_IPV6_SOURCES, config.OUT_SOURCE_RULESET_DIR)
