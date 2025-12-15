# 懒人版食用说明

TO-DO: 更新 MIHOMO 和 Clash 相关说明

## Surge

1. 订阅远程代理：`https://api.isteed.cc/sub?target=surge&url=` + `你的 Surge 订阅地址`
2. 打开 `首页` - `修改` 中的 `MitM`、`Rewrite` 和 `脚本`
3. 在 `MitM` 中生成并安装证书
4. Enjoy ～

## Mihomo

1. 订阅远程代理：`https://api.isteed.cc/sub?target=mihomo&url=` + `你的 Mihomo 订阅地址`
2. Enjoy ～

## Clash

建议使用 Mihomo 内核系软件，不再建议使用 Clash

配置文件**已弃用**

1. 订阅远程代理：`https://api.isteed.cc/sub?target=clash&url=` + `你的 Clash 订阅地址`
2. Enjoy ～

# 进阶使用说明

带 `target` 参数既生成对应的配置文件，不带则只生成 NodeList

以及组合订阅方法（可兼容超过三个的订阅）

```
https://api.isteed.cc/sub?url=[你的第一个订阅链接]|[你的第二个订阅链接]&name=[第一个订阅链接的显示名]|[第二个订阅链接的显示名]&target=[目标配置]
```

# 手动版食用说明

## Surge

Surge 于 2024-04-03 的 5.21.0 (**3088**) 新增了智能策略组，若 Surge 低于此版本，请使用 [Autotest 兼容配置](https://ruleset.isteed.cc/Config/surge-autotest.conf)

---

[Surge 配置](https://ruleset.isteed.cc/Config/surge.conf)要求较新版本的 Surge（iOS **4.13.0** 或 Mac **4.5.2** 以上）

这个版本更新了以下功能，本配置中用于处理订阅链接

- `You can now use a full profile as the external policy group (policy-path). All proxies in the [Proxy] section will be used.`

配置使用方法：将 [Proxy Group] 中的 `https://example.com/sub` 替换为你的订阅地址

## Mihomo

Mihomo 内核可使用 `proxy-providers` 与 `rule-providers`，~~本配置可搭配个人自建 API 来提取订阅中的 NodeList~~ Mihomo 官方已支持直接使用订阅链接

~~配置使用方法：将 `proxy-providers` 下的 `ProxyList` 中的 `https://example.com/nodelist` 替换为 `https://api.isteed.cc/sub?url=` + 你的订阅地址~~

~~例如你的订阅地址为 `https://example.com/api/v1/client/subscribe?token=1145141919810`~~

~~那就将配置文件中的 `https://example.com/nodelist` 替换为 `https://api.isteed.cc/sub?url=https://example.com/api/v1/client/subscribe?token=1145141919810` 即可~~

# 策略组说明

策略组是可以嵌套选择的，比如现在有个 `PROXY` 策略组，这个策略组选择了 `EXAMPLE` 策略组，而 `EXAMPLE` 策略组选择了 `TEST` 策略组，`TEST` 策略组选择了 `HK1`

则整个链路为 `PROXY` -> `EXAMPLE` -> `TEST` -> `HK1`，既最后为 `HK1` 在起作用

<!-- prettier-ignore -->
| 策略组 | 默认值 | 说明 |
|:-|:-|:-|
| 代理 | 自动测试 | 选择你需要的代理，默认自动测试，可以手动选择你需要的 |
| 直连 | - | 常用与国内网站，不需要走代理的东西 |
| 自动测试 | - | 自动测试延迟最低的节点并使用 |
| 自动回退 | - | 按照代理列表顺序依次测试，若不可用则切换到下一个 |
| 流媒体 | 代理 | 大部分海外流媒体平台，如 Netflix |
| 港澳台流媒体 | 直连 | 在大陆提供服务，但港澳台有限定资源的流媒体，如哔哩哔哩 |
| 部分 AI 服务 | 代理 | ChatGPT、Claude 和 Gemini 等 |
| Apple | 直连 | Apple 及其相关服务 |
| Telegram | 代理 | Telegram 及其相关服务 |
| OneDrive | 直连 | OneDrive 及其相关服务 |
| 广告拦截 | 拒绝 | 拒绝连接，常用于广告拦截 |
| 匹配 | 代理 | 黑白名单制，选择的即为没有规则匹配到时走的 |

# 策略组名称对照表

<!-- prettier-ignore -->
| 策略组 | Clash 策略组 | Surge 策略组 |
|:-|:-|:-|
| 代理 | `𝑃𝑟𝑜𝑥𝑦` | `𝑃𝑟𝑜𝑥𝑦` |
| 直连 | `𝐷𝑖𝑟𝑒𝑐𝑡` | `𝐷𝑖𝑟𝑒𝑐𝑡` |
| 拒绝 | `𝑅𝑒𝑗𝑒𝑐𝑡` | `𝑅𝑒𝑗𝑒𝑐𝑡` |
| 自动测试 | `𝐴𝑢𝑡𝑜𝑡𝑒𝑠𝑡` | 暂无 |
| 自动回退 | `𝐹𝑎𝑙𝑙𝑏𝑎𝑐𝑘` | 暂无 |
| 智能策略 | 暂无 | `𝑆𝑚𝑎𝑟𝑡` |
| 智能香港 | 暂无 | `𝑆𝑚𝑎𝑟𝑡𝐻𝐾` |
| 智能日本 | 暂无 | `𝑆𝑚𝑎𝑟𝑡𝐽𝑃` |
| 智能新加坡 | 暂无 | `𝑆𝑚𝑎𝑟𝑡𝑆𝐺` |
| 流媒体 | `𝑆𝑡𝑟𝑒𝑎𝑚𝑖𝑛𝑔` | `𝑆𝑡𝑟𝑒𝑎𝑚𝑖𝑛𝑔` |
| 港澳台流媒体 | `𝑆𝑡𝑟𝑒𝑎𝑚𝑖𝑛𝑔𝑆𝐸` | `𝑆𝑡𝑟𝑒𝑎𝑚𝑖𝑛𝑔𝑆𝐸` |
| Telegram | `𝑇𝑒𝑙𝑒𝑔𝑟𝑎𝑚` | `𝑇𝑒𝑙𝑒𝑔𝑟𝑎𝑚` |
| 部分 AI 服务 | `𝐴𝐼` | `𝐴𝐼` |
| Apple | `𝐴𝑝𝑝𝑙𝑒` | `𝐴𝑝𝑝𝑙𝑒` |
| OneDrive | `𝑂𝑛𝑒𝐷𝑟𝑖𝑣𝑒` | `𝑂𝑛𝑒𝐷𝑟𝑖𝑣𝑒` |
| 广告拦截 | `𝐺𝑢𝑎𝑟𝑑` | `𝐺𝑢𝑎𝑟𝑑` |
| 匹配 | `𝐹𝑖𝑛𝑎𝑙` | `𝐹𝑖𝑛𝑎𝑙` |
