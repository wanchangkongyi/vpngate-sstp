#!/usr/bin/env python3
"""
VPN Gate SSTP 节点每日抓取脚本

思路：
  - VPNGate API 返回每个节点的 OpenVPN base64 配置
  - 配置里的 "remote hostname PORT" 就是 SoftEther 监听端口
  - SSTP 和 SoftEther SSL-VPN 共用同一个 HTTPS 端口
  - 所以从 ovpn 配置提取端口即为 SSTP 端口

输出格式: sstp://vpn:vpn@hostname:port
"""

import csv
import io
import sys
import base64
import re
import logging
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError

API_URL  = "https://www.vpngate.net/api/iphone/"
OUTPUT   = "ip.txt"
HEADERS  = {"User-Agent": "Mozilla/5.0 (compatible; vpngate-fetcher/1.0)"}

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)


def fetch_raw(url: str, timeout: int = 30) -> str:
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_port_from_ovpn(b64: str) -> int:
    """从 base64 编码的 .ovpn 配置提取端口号，默认 443。"""
    try:
        cfg = base64.b64decode(b64).decode("utf-8", errors="replace")
        # 找 "remote hostname PORT" 这行
        m = re.search(r'^remote\s+\S+\s+(\d+)', cfg, re.MULTILINE)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return 443


def parse_servers(raw: str) -> list:
    lines = [l for l in raw.splitlines() if not l.startswith("*")]
    reader = csv.DictReader(io.StringIO("\n".join(lines)))
    results = []
    for row in reader:
        hostname = row.get("#HostName", "").strip()
        b64      = row.get("OpenVPN_ConfigData_Base64", "").strip()
        if not hostname:
            continue
        port = extract_port_from_ovpn(b64) if b64 else 443
        results.append(f"sstp://vpn:vpn@{hostname}:{port}")
    return results


def main():
    try:
        log.info("正在抓取 VPNGate 节点列表...")
        raw     = fetch_raw(API_URL)
        lines   = parse_servers(raw)
        log.info("共获取 %d 个节点", len(lines))

        if not lines:
            log.error("未解析到任何节点")
            sys.exit(1)

        updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        content = (
            f"# VPNGate SSTP 节点列表\n"
            f"# 更新时间: {updated_at}\n"
            f"# 共 {len(lines)} 个节点\n\n"
        ) + "\n".join(lines) + "\n"

        with open(OUTPUT, "w", encoding="utf-8") as f:
            f.write(content)
        log.info("已写入 %s", OUTPUT)

        log.info("前 5 条预览:")
        for line in lines[:5]:
            log.info("  %s", line)

    except URLError as e:
        log.error("网络请求失败: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
