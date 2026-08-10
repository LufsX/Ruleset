import os
from pathlib import Path

"""
配置相关
"""

PROXY_SETTING = os.getenv("PROXY_SETTING", "False").lower() in ("true", "1")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", None)

PROCESS_DIR = os.fspath(Path(__file__).resolve().parent.parent)
RULESET_DIR = os.path.join(PROCESS_DIR, "List")

OUT_DIR = os.path.join(PROCESS_DIR, "Public")
OUT_RULESET_DIR = os.path.join(OUT_DIR, "List")

OUT_SOURCE_RULESET_DIR = os.path.join(OUT_DIR, "List", "Source")
OUT_SINGBOX_RULESET_DIR = os.path.join(OUT_RULESET_DIR, "sing-box")
OUT_CLASH_RULESET_DIR = os.path.join(OUT_RULESET_DIR, "Clash")
OUT_SURGE_RULESET_DIR = os.path.join(OUT_RULESET_DIR, "Surge")
OUT_SMARTDNS_RULESET_DIR = os.path.join(OUT_RULESET_DIR, "smartdns")
OUT_MIHOMO_RULESET_DIR = os.path.join(OUT_RULESET_DIR, "mihomo")

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
    "BankHK_AntBank.conf",
    "BankHK_BOCHK.conf",
    "BankHK_CNCBI.conf",
    "BankHK_EleBank.conf",
    "BankHK_Fusion.conf",
    "BankHK_HSBCHK.conf",
    "BankHK_ICBCA.conf",
    "BankHK_NCB.conf",
    "BankHK_PAOBank.conf",
    "BankHK_WeLab.conf",
    "BankHK_ZABank.conf",
]

"""
文件相关
"""

COPY_PATH = ("Config", "Mock", "Script", "Module", "vercel.json")

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

"""
Web相关
"""

WEB_RULE_EXTENSIONS = [".conf", ".json", ".txt"]

"""
处理相关
"""

def with_proxy(url: str) -> str:
    proxy_prefix = "https://cors.isteed.cc/"
    if not PROXY_SETTING or url.startswith(proxy_prefix):
        return url
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"Unsupported source URL: {url}")
    return proxy_prefix + url


if PROXY_SETTING:

    DNSMASQ_CHINA_LIST = {
        name: with_proxy(link) for name, link in DNSMASQ_CHINA_LIST.items()
    }
    CHINA_IP_SOURCES = [with_proxy(source) for source in CHINA_IP_SOURCES]
    CHINA_IPV6_SOURCES = [with_proxy(source) for source in CHINA_IPV6_SOURCES]
    GUARD_SOURCES = [with_proxy(source) for source in GUARD_SOURCES]
