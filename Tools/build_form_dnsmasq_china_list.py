import os
import re

from pipeline import BuildStage, PluginSpec, TaskSpec
import until


def download_and_process(name, link, out_dir) -> None:
    print(f"[dnsmasq] Start download and process {name}")
    content = until.fetch_text(link)

    update_info = until.make_build_header(f"{name} List", [link])

    pattern = re.compile(r"^server=/(.+?)/", re.MULTILINE)
    matches = pattern.findall(content)

    output_path = os.path.join(out_dir, f"{name}.conf")
    until.write_lines_with_header(output_path, update_info, matches)

    print(f"[dnsmasq] End downloading and processing {name}")


def build(dnsmasq_china_list, out_dir) -> None:
    print("[dnsmasq] Start building from dnsmasq china list…")

    download_functions = [
        lambda name=name, link=link: download_and_process(name, link, out_dir)
        for name, link in dnsmasq_china_list.items()
    ]

    until.run_in_threads(download_functions)

    print("[dnsmasq] End building from dnsmasq china list")


def _run(context) -> None:
    build(
        context.config.DNSMASQ_CHINA_LIST,
        os.fspath(context.paths.source_rules),
    )


PLUGIN = PluginSpec(
    id="dnsmasq",
    tasks=(
        TaskSpec(
            id="source.dnsmasq",
            stage=BuildStage.SOURCE,
            action=_run,
            writes=frozenset(
                {
                    "List/Source/ChinaApple.conf",
                    "List/Source/ChinaDomain.conf",
                    "List/Source/ChinaGoogle.conf",
                }
            ),
        ),
    ),
)


if __name__ == "__main__":
    import config

    build(config.DNSMASQ_CHINA_LIST, config.OUT_SOURCE_RULESET_DIR)
