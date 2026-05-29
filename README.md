# VPNGate SSTP 节点每日自动更新

每天自动从 [VPN Gate](https://www.vpngate.net) 抓取公共 VPN 节点，筛选 SSTP 协议并写入 Gist。

## 订阅地址

通过 Cloudflare Worker 绑定自定义域名后访问：

```
https://bpsub.194216.xyz/vpn
```

## 节点格式

```
sstp://vpn:vpn@public-vpn-120.opengw.net:443#JP
sstp://vpn:vpn@vpn924983651.opengw.net:1442#US
sstp://vpn:vpn@vpn519731163.opengw.net:1598#KR
```

## 字段说明

| 字段 | 说明 |
|------|------|
| 协议 | `sstp` |
| 用户名 | `vpn`（固定） |
| 密码 | `vpn`（固定） |
| 主机名 | VPN Gate 节点域名 |
| 端口 | 节点实际 TCP 端口 |
| `#XX` | 国家代码备注 |

## 更新频率

每天 **北京时间 09:00** 自动运行，也可在 Actions 页面手动触发。

## 数据来源

[VPN Gate Academic Experiment Service](https://www.vpngate.net) — 日本筑波大学学术实验项目
