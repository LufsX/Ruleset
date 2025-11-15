import datetime

start_time = datetime.datetime.now()

import config
import os
import shutil
import until

OUT_DIR: str = config.OUT_DIR
INIT_DIR_NAME: tuple = config.INIT_DIR_NAME
COPY_PATH: tuple = config.COPY_PATH
COPY_SOURCE_PATH: dict = config.COPY_SOURCE_PATH
PROCESS_DIR: str = config.PROCESS_DIR
RULESET_DIR: str = config.RULESET_DIR
OUT_RULESET_DIR: str = config.OUT_RULESET_DIR
OUT_SOURCE_RULESET_DIR: str = config.OUT_SOURCE_RULESET_DIR


def init() -> None:
    if os.path.exists(OUT_DIR):
        print("[Build] Clear the last generated files…")
        shutil.rmtree(OUT_DIR)
    for dir_name in INIT_DIR_NAME:
        os.makedirs(os.path.join(OUT_DIR, dir_name))


def copy_files() -> None:
    print("[Build] Copy files that do not need to be generated…")
    for path in COPY_PATH:
        src, dest = os.path.join(PROCESS_DIR, path), os.path.join(OUT_DIR, path)
        (
            shutil.copytree(src, dest, dirs_exist_ok=True)
            if os.path.isdir(src)
            else shutil.copy2(src, dest)
        )

    for src, dest in COPY_SOURCE_PATH.items():
        shutil.copytree(
            os.path.join(PROCESS_DIR, src),
            os.path.join(OUT_SOURCE_RULESET_DIR, dest),
            dirs_exist_ok=True,
        )


def clear_config_comment() -> None:
    print("[Build] Start clearing config comment…")

    for src, dest in config.CONFIG_FILE_CLEAR.items():
        until.clear_comment(src, dest)

    print("[Build] End clearing config comment")


def build_form_dnsmasq_china_list() -> None:
    import build_form_dnsmasq_china_list

    build_form_dnsmasq_china_list.build(
        config.DNSMASQ_CHINA_LIST, OUT_SOURCE_RULESET_DIR
    )


def build_smartdns() -> None:
    import build_smartdns

    build_smartdns.build(config.SMARTDNS_FILE, OUT_SOURCE_RULESET_DIR)


def build_china_ip() -> None:
    import build_china_ip

    build_china_ip.build(config.CHINA_IP_SOURCES, OUT_SOURCE_RULESET_DIR)


def build_china_ipv6() -> None:
    import build_china_ipv6

    build_china_ipv6.build(config.CHINA_IPV6_SOURCES, OUT_SOURCE_RULESET_DIR)


def build_guard() -> None:
    import build_guard

    build_guard.build(config.GUARD_SOURCES, OUT_SOURCE_RULESET_DIR)


def build_singbox() -> None:
    import build_singbox

    build_singbox.build(OUT_SOURCE_RULESET_DIR, config.OUT_SINGBOX_RULESET_DIR)


def build_surge() -> None:
    import build_surge

    build_surge.build(OUT_SOURCE_RULESET_DIR, config.OUT_SURGE_RULESET_DIR)


def build_clash() -> None:
    import build_clash

    build_clash.build(OUT_SOURCE_RULESET_DIR, config.OUT_CLASH_RULESET_DIR)


def build_bankhk() -> None:
    import build_bankhk

    build_bankhk.build(config.BANKHK_SOURCES, RULESET_DIR, OUT_SOURCE_RULESET_DIR)


def convert_markdown() -> None:
    import build_web

    build_web.convert_all_markdown_files(
        config.OUT_DIR, github_token=config.GITHUB_TOKEN
    )


def build_web() -> None:
    import build_web

    build_web.build_file_list_page(
        config.OUT_DIR,
        os.path.join(config.OUT_DIR, "index.html"),
        github_token=config.GITHUB_TOKEN,
        rule_extensions=config.WEB_RULE_EXTENSIONS,
    )


init()
copy_files()
for src, dest in config.COPY_FILE.items():
    shutil.copy2(src, dest)
for src, dest in config.README_FILE.items():
    shutil.move(src, dest)

until.run_in_threads(
    [
        clear_config_comment,
        build_form_dnsmasq_china_list,
        build_china_ip,
        build_china_ipv6,
        build_guard,
        build_bankhk,
    ]
)

until.run_in_threads(
    [
        build_singbox,
        build_smartdns,
        build_surge,
        build_clash,
    ]
)

convert_markdown()
build_web()

end_time = datetime.datetime.now()

print(f"Total time: {end_time - start_time}")
