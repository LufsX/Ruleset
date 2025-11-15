import os
import sys

"""
配置相关
"""

PROXY_SETTING = os.getenv("PROXY_SETTING", "False").lower() in ("true", "1")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", None)

PROCESS_DIR = os.path.abspath(os.path.dirname(sys.path[0]))
RULESET_DIR = os.path.join(PROCESS_DIR, "List")

OUT_DIR = os.path.join(PROCESS_DIR, "Public")
OUT_RULESET_DIR = os.path.join(OUT_DIR, "List")

OUT_SOURCE_RULESET_DIR = os.path.join(OUT_DIR, "List", "Source")
OUT_SINGBOX_RULESET_DIR = os.path.join(OUT_RULESET_DIR, "sing-box")
OUT_CLASH_RULESET_DIR = os.path.join(OUT_RULESET_DIR, "Clash")
OUT_SURGE_RULESET_DIR = os.path.join(OUT_RULESET_DIR, "Surge")
OUT_SMARTDNS_RULESET_DIR = os.path.join(OUT_RULESET_DIR, "smartdns")

DNSMASQ_CHINA_LIST = {
    "ChinaDomain": "https://github.com/felixonmars/dnsmasq-china-list/raw/master/accelerated-domains.china.conf",
    "ChinaApple": "https://github.com/felixonmars/dnsmasq-china-list/raw/master/apple.china.conf",
    "ChinaGoogle": "https://github.com/felixonmars/dnsmasq-china-list/raw/master/google.china.conf",
}

CHINA_IP_SOURCES = [
    "https://github.com/misakaio/chnroutes2/raw/master/chnroutes.txt",
    "https://github.com/17mon/china_ip_list/raw/master/china_ip_list.txt",
    "https://ispip.clang.cn/all_cn_cidr.txt",
]

CHINA_IPV6_SOURCES = ["https://gaoyifan.github.io/china-operator-ip/china6.txt"]

GUARD_SOURCES = [
    "https://github.com/SukkaW/Surge/raw/master/Source/domainset/reject.conf",
    "https://github.com/TG-Twilight/AWAvenue-Ads-Rule/raw/main/Filters/AWAvenue-Ads-Rule-Surge.list",
]

BANKHK_SOURCES = [
    "BankHK_AirStar.conf",
    "BankHK_AntBank.conf",
    "BankHK_BOCHK.conf",
    "BankHK_CNCBI.conf",
    "BankHK_Fusion.conf",
    "BankHK_HSBCHK.conf",
    "BankHK_ICBCA.conf",
    "BankHK_PAOBank.conf",
    "BankHK_WeLab.conf",
    "BankHK_ZABank.conf",
]

"""
文件相关
"""

INIT_DIR_NAME = (
    os.path.join("List", "Clash"),
    os.path.join("List", "Source"),
    os.path.join("List", "Surge"),
    os.path.join("List", "smartdns"),
)

COPY_PATH = ("Config", "Mock", "Script", "Module", "vercel.json")
COPY_SOURCE_PATH = {RULESET_DIR: OUT_SOURCE_RULESET_DIR}

CONFIG_FILE_CLEAR = {
    os.path.join(OUT_DIR, "Config", "clash.yaml"): os.path.join(
        OUT_DIR, "Config", "clash-nocomment.yaml"
    ),
    os.path.join(OUT_DIR, "Config", "surge.conf"): os.path.join(
        OUT_DIR, "Config", "surge-nocomment.conf"
    ),
    os.path.join(OUT_DIR, "Config", "surge-autotest.conf"): os.path.join(
        OUT_DIR, "Config", "surge-autotest-nocomment.conf"
    ),
    os.path.join(OUT_DIR, "Config", "mihomo.yaml"): os.path.join(
        OUT_DIR, "Config", "mihomo-nocomment.yaml"
    ),
}

SMARTDNS_FILE = {
    os.path.join(OUT_SOURCE_RULESET_DIR, "Guard.conf"): os.path.join(
        OUT_SMARTDNS_RULESET_DIR, "Guard.txt"
    ),
    os.path.join(OUT_SOURCE_RULESET_DIR, "ChinaApple.conf"): os.path.join(
        OUT_SMARTDNS_RULESET_DIR, "ChinaApple.txt"
    ),
    os.path.join(OUT_SOURCE_RULESET_DIR, "ChinaDomain.conf"): os.path.join(
        OUT_SMARTDNS_RULESET_DIR, "ChinaDomain.txt"
    ),
    os.path.join(OUT_SOURCE_RULESET_DIR, "ChinaGoogle.conf"): os.path.join(
        OUT_SMARTDNS_RULESET_DIR, "ChinaGoogle.txt"
    ),
}

README_FILE = {
    os.path.join(OUT_SOURCE_RULESET_DIR, "README.md"): os.path.join(
        OUT_RULESET_DIR, "README.md"
    ),
}

COPY_FILE = {
    os.path.join(PROCESS_DIR, "LICENSE"): os.path.join(OUT_DIR, "LICENSE"),
}

"""
Web相关
"""

WEB_RULE_EXTENSIONS = [".conf", ".json", ".txt"]

"""
处理相关
"""

if PROXY_SETTING:
    proxy_prefix = "https://cors.isteed.cc/"

    DNSMASQ_CHINA_LIST = {
        name: proxy_prefix + link for name, link in DNSMASQ_CHINA_LIST.items()
    }
    CHINA_IP_SOURCES = [proxy_prefix + source for source in CHINA_IP_SOURCES]
    CHINA_IPV6_SOURCES = [proxy_prefix + source for source in CHINA_IPV6_SOURCES]
    GUARD_SOURCES = [proxy_prefix + source for source in GUARD_SOURCES]
