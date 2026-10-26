#!/usr/bin/env python3
# Wildcard · 拉取 Luma 官方日历（kimiambassadorevent）自动同步的活动
# 数据源：Supabase wildcard-kimi-events / synced_events（每小时由 luma-sync 更新，公开只读）
# 用法：python3 /path/to/wildcard-for-kimi/scripts/fetch_synced_events.py [过去多少小时内开始的，默认 12]
# 输出：{"count": N, "events": [...]}（按开始时间升序；时间均为 UTC ISO）
import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

REST_URL = "https://toyyeavsdjmlqmvlrhdg.supabase.co/rest/v1/synced_events"
# anon key：只读 synced_events（RLS 限制），可随插件分发
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRveXllYXZzZGptbHFtdmxyaGRnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTEwNDMyNTUsImV4cCI6MjEwNjYxOTI1NX0.hplQdARcg_gyluzLTJR6nQNgrBzRACSeMYJSSuuaddM"


def main() -> None:
    hours = float(sys.argv[1]) if len(sys.argv) > 1 else 12
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    req = urllib.request.Request(
        f"{REST_URL}?select=api_id,title,city,venue,start_at,end_at,timezone,location_type,url,cover_url"
        f"&start_at=gte.{since}&order=start_at.asc",
        headers={"apikey": ANON_KEY, "Authorization": f"Bearer {ANON_KEY}"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        events = json.loads(resp.read().decode("utf-8"))
    print(json.dumps({"count": len(events), "since_utc": since, "events": events}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
