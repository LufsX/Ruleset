# 分流

有这几个地方的文件

- `List/Source/*.conf`
  - 原始规则
- `List/Clash/*.conf`
  - 基于原始规则添加了对 domainset 的 Mihomo/Clash 格式适配
- `List/Surge/*.conf`
  - 基于原始规则仅简单去掉了注释和空行
- `List/sing-box/*.json`
  - 基于原始规则制作的对应 sing-box 的规则格式
- `List/smartdns/*.txt`
  - 基于 dnsmasq_china_list 和原始规则中的 Guard.conf 的 smartdns 所用的 domainset 格式
  - 仅包含部分规则（`ChinaApple`、`ChinaDomain`、`ChinaGoogle`、`Guard` 规则）

---

注意 ⚠️: 已剔除了 YAML 格式的 Clash 规则支持，最后的版本可见[该 commit](https://github.com/LufsX/Ruleset/tree/4b5a19c07e4de5872db18064c281ee9c34c747cc/List/Clash)

---

目前（2025-11-13）所有规则及其比例如下

- DOMAIN-SUFFIX: 122140 (93.10%)
- IP-CIDR: 7303 (5.57%)
- IP-CIDR6: 1435 (1.09%)
- DOMAIN: 253 (0.19%)
- DOMAIN-KEYWORD: 42 (0.03%)
- PROCESS-NAME: 25 (0.02%)

规则中仅 `ChinaIP` 和 `ChinaIPv6` 无 `no-resolve` 标记，这两个规则务必在所有规则之后，以避免不必要的 DNS 解析

## 默认配置

以下是默认配置中包含的规则集：

<!-- prettier-ignore -->
| 名称 | 用途 |
|:-|:-|
| Apple.conf | Apple 相关内容服务|
| AppleCDN.conf | Apple 相关 CDN |
| ChatAI.conf | 部分 AI 聊天服务 |
| China.conf | 大陆正常访问的服务 |
| ChinaIP.conf | 大陆 IPv4 集 |
| ChinaIPv6.conf | 大陆 IPv6 集 |
| DirectCustom.conf | 自用直连/补充集 |
| Global.conf | 代理集 |
| Guard.conf | 去广告/隐私保护 |
| OneDrive.conf | OneDrive 可直连集 |
| ProxyCustom.conf | 自用代理/补充集 |
| Streaming.conf | 流媒体服务集 |
| StreamingSE.conf | 港澳台流媒体服务集（不含 B 站 CDN） |
| Telegram.conf | Telegram 相关 |
| Unbreak.conf | 部分需要不间断连接的域名 |

## 按需配置

以下规则集暂未加入默认配置中，需要的可以自行添加：

<!-- prettier-ignore -->
| 名称 | 用途 |
| :- | :- |
| Gamer.conf | 游戏平台 |
| MyFin.conf | MyFin 相关 |
| N26.conf | N26 相关 |
| StreamingSE&CDN.conf | 流媒体服务集（含 B 站的 CDN） |
| WARP.conf | Cloudflare WARP 相关 |
| Wise.conf | Wise 相关 |
| AppleIntelligence.conf | Apple 智能服务，务必添加在 Apple.conf 上方 |

<!-- prettier-ignore -->
| 名称 | 用途 |
| :- | :- |
| BankHK.conf | 包括常见的香港银行 |
| BankHK_AirStar.conf | 天星银行 相关 |
| BankHK_AntBank.conf | 螞蟻銀行 相关 |
| BankHK_BOCHK.conf | BOCHK 中銀香港 相关 |
| BankHK_CNCBI.conf | 中信银行国际 相关 |
| BankHK_Fusion.conf | Fusion Bank 相关 |
| BankHK_HSBCHK.conf | HSBC HK 相关 |
| BankHK_ICBCA.conf | 工银亚洲 相关 |
| BankHK_PAOBank.conf | PAOBank 相关 |
| BankHK_WeLab.conf | Welab Bank 相关 |
| BankHK_ZABank.conf | ZA Bank 相关 |
