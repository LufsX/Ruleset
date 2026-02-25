import os
import requests

import until
from until import run_in_threads


def download_and_process(link, exclude) -> list[str]:
    print(f"[Guard] Downloading and processing {link} ...")

    # 替换不可见字符表
    trans_table = str.maketrans({"\u200b": None, "\u200c": None})

    lines = []
    for line in requests.get(link).text.splitlines():
        line = line.translate(trans_table).split("#", 1)[0].strip()
        if line and line not in exclude:
            lines.append(line)
    return lines


def build(guard_sources, out_dir) -> None:
    print("[Guard] Start building from Guard sources…")

    update_info = until.make_build_header("Guard List", guard_sources)
    exclude = ("", "switch.cup.com.cn", ".amazonaws.com")
    include = ("msmp.abchina.com.cn",)
    all_lines: set[str] = set() if not include else set(include)

    def download_and_process_wrapper(link, exclude):
        lines = download_and_process(link, exclude)
        all_lines.update(lines)

    download_functions = [
        lambda link=link: download_and_process_wrapper(link, exclude)
        for link in guard_sources
    ]

    run_in_threads(download_functions)

    with open(os.path.join(out_dir, "Guard.conf"), "w", newline="\n") as f:
        f.write(update_info)
        sorted_lines = sorted(all_lines)
        f.write("\n".join(sorted_lines))
        f.write("\n")

    print(f"[Guard] End building from Guard sources, {len(all_lines)} lines")


if __name__ == "__main__":
    import config

    build(config.GUARD_SOURCES, config.OUT_SOURCE_RULESET_DIR)
