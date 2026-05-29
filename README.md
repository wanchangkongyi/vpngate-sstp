# VPNGate SSTP 节点每日自动更新

每天自动从 [VPN Gate](https://www.vpngate.net) 抓取公共 VPN 节点，筛选 SSTP 协议并写入 Gist。

## 订阅地址

通过 Cloudflare Worker 绑定自定义域名后访问：

```
https://vpn.yourdomain.com/sub
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

## 部署说明

### 1. 创建 Gist

前往 [gist.github.com](https://gist.github.com) 新建一个 Gist，文件名填 `ip.txt`，记录 Gist ID（URL 最后一段）。

### 2. 创建 Token

前往 [github.com/settings/tokens](https://github.com/settings/tokens)，新建 Classic Token，只勾选 `gist` 权限。

### 3. 配置 Secrets

在仓库 **Settings → Secrets → Actions** 添加：

| Name | Value |
|------|-------|
| `GIST_ID` | 第一步的 Gist ID |
| `GIST_TOKEN` | 第二步的 Token |

### 4. 配置 Cloudflare Worker

新建 Worker，代码如下：

```js
export default {
  async fetch(request) {
    const gistUrl = "https://gist.githubusercontent.com/你的用户名/GIST_ID/raw/ip.txt";
    const resp = await fetch(gistUrl);
    const text = await resp.text();
    return new Response(text, {
      headers: { "Content-Type": "text/plain; charset=utf-8" }
    });
  }
}
```

在 Worker 的 **Triggers → Routes** 绑定路由：

```
vpn.yourdomain.com/sub
```

## 数据来源

[VPN Gate Academic Experiment Service](https://www.vpngate.net) — 日本筑波大学学术实验项目
