#!/usr/bin/env python3
"""
VPN Gate SSTP 节点每日抓取脚本
输出格式: sstp://vpn:vpn@hostname:443
"""

import csv
import io
import sys
import logging
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError

API_URL   = "https://www.vpngate.net/api/iphone/"
OUTPUT    = "ip.txt"
SSTP_PORT = 443
HEADERS   = {"User-Agent": "Mozilla/5.0 (compatible; vpngate-fetcher/1.0)"}

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)


def fetch_raw(url: str, timeout: int = 30) -> str:
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_sstp(raw: str) -> list:
    lines = [l for l in raw.splitlines() if not l.startswith("*")]
    reader = csv.DictReader(io.StringIO("\n".join(lines)))
    results = []
    for row in reader:
        if row.get("SSTP", "").strip().lower() != "true":
            continue
        hostname = row.get("#HostName", "").strip()
        if not hostname:
            continue
        results.append(f"sstp://vpn:vpn@{hostname}:{SSTP_PORT}")
    return results


def main():
    try:
        log.info("正在抓取 VPNGate 节点列表...")
        raw   = fetch_raw(API_URL)
        lines = parse_sstp(raw)
        log.info("找到 %d 个 SSTP 节点", len(lines))

        updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        content = (
            f"# VPNGate SSTP 节点列表\n"
            f"# 更新时间: {updated_at}\n"
            f"# 共 {len(lines)} 个节点\n\n"
        ) + "\n".join(lines) + "\n"

        with open(OUTPUT, "w", encoding="utf-8") as f:
            f.write(content)
        log.info("已写入 %s", OUTPUT)

    except URLError as e:
        log.error("网络请求失败: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
