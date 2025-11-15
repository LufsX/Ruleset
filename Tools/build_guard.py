import datetime
import os
import requests

from until import run_in_threads


def download_and_process(link, exclude) -> list[str]:
    print(f"[Guard] Downloading and processing {link} ...")
    content = requests.get(link).text
    lines = [
        line
        for line in content.split("\n")
        if line and not line.startswith("#") and line.strip() not in exclude
    ]
    return lines


def build(guard_sources, out_dir) -> None:
    print("[Guard] Start building from Guard sources…")

    update_info = f'''#####################
# Guard List
# Last Updated: {(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%S") + "+08:00"}
#
# Build form:
{'\n'.join([f"#  - {link}" for link in guard_sources])}
#####################
'''
    exclude = {"", "switch.cup.com.cn", ".amazonaws.com"}
    all_lines: set[str] = set()

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
