#!/usr/bin/env python3
"""
VPN Gate SSTP 节点每日抓取脚本
- 主机名: #HostName + .opengw.net
- 端口:   从 ovpn 配置提取 TCP 端口（SSTP 必须走 TCP）
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
DOMAIN   = ".opengw.net"
HEADERS  = {"User-Agent": "Mozilla/5.0 (compatible; vpngate-fetcher/1.0)"}

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)


def fetch_raw(url: str, timeout: int = 30) -> str:
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_tcp_port(b64: str) -> int:
    """
    从 ovpn 配置提取 TCP 端口。
    ovpn 里可能有多个 remote 行对应不同协议/端口，
    SSTP 必须走 TCP，所以找 proto tcp 对应的那个端口。
    
    SoftEther 生成的 ovpn 格式：
      remote IP PORT1   <- TCP
      remote IP PORT2   <- UDP（如果有）
      proto tcp / proto udp 交替出现
    或者只有一种协议。
    """
    try:
        cfg = base64.b64decode(b64).decode("utf-8", errors="replace")
        lines = cfg.splitlines()

        # 收集所有 remote 行（按顺序）
        remotes = []
        for line in lines:
            line = line.strip()
            m = re.match(r'^remote\s+\S+\s+(\d+)', line)
            if m:
                remotes.append(int(m.group(1)))

        if not remotes:
            return 443

        # 如果只有一种端口（或所有端口相同），直接返回
        unique = list(dict.fromkeys(remotes))
        if len(unique) == 1:
            return unique[0]

        # 有多个不同端口：排除 UDP 常见端口（1194），取非 UDP 端口
        # UDP VPN 常用端口: 1194, 1195, 1196 等
        UDP_PORTS = {1194, 1195, 1196, 1197, 1198}
        tcp_candidates = [p for p in unique if p not in UDP_PORTS]
        if tcp_candidates:
            return tcp_candidates[0]

        # 兜底返回第一个
        return remotes[0]

    except Exception:
        return 443


def parse_servers(raw: str) -> list:
    lines = [l for l in raw.splitlines() if not l.startswith("*")]
    reader = csv.DictReader(io.StringIO("\n".join(lines)))
    results = []
    for row in reader:
        short_name = row.get("#HostName", "").strip()
        if not short_name:
            continue
        hostname = short_name if "." in short_name else short_name + DOMAIN
        b64     = row.get("OpenVPN_ConfigData_Base64", "").strip()
        port    = extract_tcp_port(b64) if b64 else 443
        country = row.get("CountryShort", "").strip()
        suffix  = f"#{country}" if country else ""
        results.append(f"sstp://vpn:vpn@{hostname}:{port}{suffix}")
    return results


def main():
    try:
        log.info("正在抓取 VPNGate 节点列表...")
        raw   = fetch_raw(API_URL)
        lines = parse_servers(raw)
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
