import concurrent.futures
import datetime
import os
import tempfile
import time
from collections.abc import Callable, Iterable
from typing import TypeVar

import requests


T = TypeVar("T")
HTTP_TIMEOUT = (10, 60)


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
    content = header + "\n".join(lines) + "\n"
    write_text_atomic(out_path, content)


def write_text_atomic(path: str, content: str) -> None:
    """Write a UTF-8 text file and replace the destination atomically."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=directory,
            delete=False,
        ) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        os.replace(temp_path, path)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def fetch_text(url: str, *, timeout=HTTP_TIMEOUT, retries: int = 3) -> str:
    return _request_text(
        lambda: requests.get(url, timeout=timeout), retries=retries
    )


def post_json_text(
    url: str,
    *,
    headers: dict[str, str],
    payload: dict[str, str],
    timeout=HTTP_TIMEOUT,
    retries: int = 3,
) -> str:
    return _request_text(
        lambda: requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=timeout,
        ),
        retries=retries,
    )


def _request_text(request: Callable[[], requests.Response], *, retries: int) -> str:
    if retries < 1:
        raise ValueError("retries must be at least 1")

    for attempt in range(retries):
        try:
            response = request()
            response.raise_for_status()
            return response.text
        except requests.RequestException:
            if attempt == retries - 1:
                raise
            time.sleep(0.5 * (2**attempt))

    raise AssertionError("unreachable")


def clear_comment(src_file, dest_file) -> None:
    with open(src_file, "r", encoding="utf-8") as src:
        lines = src.readlines()

    cleaned_lines = [
        cleaned
        for line in lines
        if (cleaned := _strip_inline_comment(line)).strip()
    ]

    write_text_atomic(dest_file, "".join(cleaned_lines))

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

    write_text_atomic(dest_file, "".join(output_lines))

    print(f"[Util] Deduplication for {src_file}")


def _strip_inline_comment(line: str) -> str:
    quote: str | None = None
    escaped = False
    for index, character in enumerate(line):
        if escaped:
            escaped = False
            continue
        if character == "\\" and quote == '"':
            escaped = True
            continue
        if character in ("'", '"'):
            quote = None if quote == character else character if quote is None else quote
            continue
        if character == "#" and quote is None and (
            index == 0 or line[index - 1].isspace()
        ):
            return line[:index].rstrip() + "\n"
    return line.rstrip() + "\n"


def run_in_threads(
    functions: Iterable[Callable[[], T]], *, max_workers: int | None = None
) -> list[T]:
    """Run callables concurrently, preserving result order and propagating errors."""
    tasks = list(functions)
    if not tasks:
        return []
    worker_count = max_workers or min(8, len(tasks))
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(function) for function in tasks]
        return [future.result() for future in futures]


if __name__ == "__main__":
    import config
    import os

    ruleset_dir = config.RULESET_DIR

    for root, _, files in os.walk(ruleset_dir):
        for file in files:
            if file.endswith(".conf"):
                file_path = os.path.join(root, file)
                deduplicate(file_path, file_path)
