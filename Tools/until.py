import concurrent.futures
import datetime
import re


def now_cn_iso8601() -> str:
    return (
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)
    ).strftime("%Y-%m-%dT%H:%M:%S") + "+08:00"


def make_ruleset_header(rule_name: str) -> str:
    return f"""#####################
# {rule_name}
# Last Updated: {now_cn_iso8601()}
#
# Form:
#  - https://ruleset.isteed.cc/List/Source/{rule_name}.conf
#####################
"""


def make_build_header(title: str, build_from: list[str]) -> str:
    links = "\n".join([f"#  - {item}" for item in build_from])
    return f"""#####################
# {title}
# Last Updated: {now_cn_iso8601()}
#
# Build form:
{links}
#####################
"""


def read_clean_lines(file_path: str) -> list[str]:
    """读取文件，去掉空行与整行注释（以 # 开头），并 strip。"""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.lstrip().startswith("#")
        ]


def extract_leading_comment_header(lines: list[str]) -> str | None:
    """提取文件头部连续的注释块（# 开头的行），用于复用原文件头。"""
    header_lines: list[str] = []
    for line in lines:
        if line.strip().startswith("#"):
            header_lines.append(line)
        else:
            break
    return "".join(header_lines) if header_lines else None


def write_lines_with_header(
    out_path: str,
    header: str,
    lines: list[str],
    *,
    sort_lines: bool = False,
) -> None:
    if sort_lines:
        lines = sorted(lines)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(header)
        f.write("\n".join(lines))
        f.write("\n")


def prepend_text_to_file_binary(path: str, text: str) -> None:
    prefix = text.encode("utf-8")
    with open(path, "rb") as f:
        content = f.read()
    with open(path, "wb") as f:
        f.write(prefix)
        f.write(content)


def clear_comment(src_file, dest_file) -> None:
    with open(src_file, "r", encoding="utf-8") as src:
        lines = src.readlines()

    cleaned_lines = []
    for line in lines:
        match = re.match(r"^[^#]*", line)
        if match:
            cleaned_lines.append(match.group(0).rstrip() + "\n")
        else:
            cleaned_lines.append("\n")

    cleaned_lines = [line for line in cleaned_lines if line.strip()]

    with open(dest_file, "w", encoding="utf-8", newline="\n") as dest:
        dest.writelines(filter(None, cleaned_lines))

    print(f"[Util] Clearing comments for {src_file}")


def deduplicate(src_file, dest_file) -> None:
    lines_seen = set()
    output_lines = []

    with open(src_file, "r", encoding="utf-8") as file:
        for line in file:
            stripped_line = line.strip()
            if (
                stripped_line == ""
                or stripped_line.startswith("#")
                or stripped_line not in lines_seen
            ):
                output_lines.append(line)
                if stripped_line != "":
                    lines_seen.add(stripped_line)

    with open(dest_file, "w", encoding="utf-8", newline="\n") as file:
        file.writelines(output_lines)

    print(f"[Util] Deduplication for {src_file}")


def run_in_threads(functions) -> None:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(lambda f: f(), functions)


if __name__ == "__main__":
    import config
    import os

    ruleset_dir = config.RULESET_DIR

    for root, _, files in os.walk(ruleset_dir):
        for file in files:
            if file.endswith(".conf"):
                file_path = os.path.join(root, file)
                deduplicate(file_path, file_path)
