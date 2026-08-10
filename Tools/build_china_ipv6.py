import ipaddress
import os

from pipeline import BuildStage, PluginSpec, TaskSpec
import until


def download_and_process(link, exclude) -> list[str]:
    print(f"[ChinaIPv6] Downloading and processing {link} ...")
    content = until.fetch_text(link)
    lines = [
        processed
        for line in content.splitlines()  # splitlines 处理换行符更通用
        if (processed := line.split("#", 1)[0].strip()) and processed not in exclude
    ]
    return lines


def build(china_ipv6_sources, out_dir) -> None:
    print("[ChinaIPv6] Start building from China IPv6 sources…")

    update_info = until.make_build_header("China IPv6 List", china_ipv6_sources)
    exclude = {
        # Space
        "",
    }

    download_functions = [
        lambda link=link: download_and_process(link, exclude)
        for link in china_ipv6_sources
    ]
    all_lines = {
        line
        for source_lines in until.run_in_threads(download_functions)
        for line in source_lines
    }

    all_networks = set()

    for line in all_lines:
        try:
            network = ipaddress.ip_network(line.strip(), strict=False)
            all_networks.add(network)
        except ValueError:
            print(f"[ChinaIPv6] Invalid network format: {line}")

    merged_networks = ipaddress.collapse_addresses(all_networks)

    output_path = os.path.join(out_dir, "ChinaIPv6.conf")
    output_lines = [f"IP-CIDR6,{network}" for network in merged_networks]
    until.write_lines_with_header(output_path, update_info, output_lines)

    print("[ChinaIPv6] End building from china IPv6 sources")


def _run(context) -> None:
    build(
        context.config.CHINA_IPV6_SOURCES,
        os.fspath(context.paths.source_rules),
    )


PLUGIN = PluginSpec(
    id="china-ipv6",
    tasks=(
        TaskSpec(
            id="source.china-ipv6",
            stage=BuildStage.SOURCE,
            action=_run,
            writes=frozenset({"List/Source/ChinaIPv6.conf"}),
        ),
    ),
)


if __name__ == "__main__":
    import config

    build(config.CHINA_IPV6_SOURCES, config.OUT_SOURCE_RULESET_DIR)
