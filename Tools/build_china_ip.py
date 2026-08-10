import ipaddress
import os

from pipeline import BuildStage, PluginSpec, TaskSpec
import until


def download_and_process(link, exclude) -> list[str]:
    print(f"[ChinaIP] Downloading and processing {link} ...")
    content = until.fetch_text(link)
    lines = [
        processed
        for line in content.splitlines()  # splitlines 处理换行符更通用
        if (processed := line.split("#", 1)[0].strip()) and processed not in exclude
    ]
    return lines


def build(china_ip_sources, out_dir) -> None:
    print("[ChinaIP] Start building from China IP sources…")

    update_info = until.make_build_header("China IP List", china_ip_sources)
    exclude = (
        # From https://github.com/SukkaW/chnroutes2-optimized/blob/e0f10e1f243208f2eba4b4fb20d5050dbceed17f/index.ts#L52-L73
        # China Mobile International HK
        # https://github.com/misakaio/chnroutes2/issues/25
        "223.118.0.0/15",
        "223.120.0.0/15",
        # Cloudie.hk
        # https://github.com/misakaio/chnroutes2/issues/50
        "123.254.104.0/21",
        # xTom
        # https://github.com/misakaio/chnroutes2/issues/49
        "45.147.48.0/23",
        "45.80.188.0/24",
        "45.80.190.0/24",
        # https://github.com/misakaio/chnroutes2/issues/52
        "137.220.128.0/17",
        # Cloudie.hk
        "103.246.246.0/23",
        "45.199.166.0/24",
        "45.199.167.0/24",
        # Space
        "",
    )

    download_functions = [
        lambda link=link: download_and_process(link, exclude)
        for link in china_ip_sources
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
            print(f"[ChinaIP] Invalid network format: {line}")

    merged_networks = ipaddress.collapse_addresses(all_networks)

    output_path = os.path.join(out_dir, "ChinaIP.conf")
    output_lines = [f"IP-CIDR,{network}" for network in merged_networks]
    until.write_lines_with_header(output_path, update_info, output_lines)

    print("[ChinaIP] End building from china IP sources")


def _run(context) -> None:
    build(
        context.config.CHINA_IP_SOURCES,
        os.fspath(context.paths.source_rules),
    )


PLUGIN = PluginSpec(
    id="china-ip",
    tasks=(
        TaskSpec(
            id="source.china-ip",
            stage=BuildStage.SOURCE,
            action=_run,
            writes=frozenset({"List/Source/ChinaIP.conf"}),
        ),
    ),
)


if __name__ == "__main__":
    import config

    build(config.CHINA_IP_SOURCES, config.OUT_SOURCE_RULESET_DIR)
