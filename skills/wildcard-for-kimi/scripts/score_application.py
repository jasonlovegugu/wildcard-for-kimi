#!/usr/bin/env python3
"""Wildcard 会员状态评分：只使用套餐和有效期，不读取用量或历史订单。

用法:
  python3 score_application.py '<proof-json 字符串>'
  python3 score_application.py proof.json
  echo '<json>' | python3 score_application.py -

proof JSON 字段（均可缺省）:
  plan               当前会员套餐名称，赠送套餐不区别对待
  valid_until        订阅有效期（YYYY-MM-DD）
  note               备注（"手工解析" / "人工复核"）；人工兜底进入 fast_review

输出: {"score": int, "decision": fast_pass|fast_review|standard, "reasons": [...]}
退出码恒为 0；输入非法时 decision=standard 并给出原因。
"""
import json
import re
import sys
from datetime import date


PLAN_RE = re.compile(
    r"会员|\b(?:Go|Plus|Pro|Ultra|Max|Allegro|Allegretto|Moderato|Andante)\b|付费|premium",
    re.I,
)


def load_proof() -> dict:
    arg = sys.argv[1] if len(sys.argv) > 1 else "-"
    try:
        raw = sys.stdin.read() if arg == "-" else (open(arg, encoding="utf-8").read() if arg.endswith(".json") else arg)
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def main() -> None:
    proof = load_proof()
    score, reasons = 0, []

    plan = str(proof.get("plan") or "")
    if PLAN_RE.search(plan):
        score += 40
        reasons.append(f"会员套餐(+40): {plan}")

    valid_until = str(proof.get("valid_until") or "")
    match = re.match(r"(20\d{2})-(\d{2})-(\d{2})", valid_until)
    if match:
        try:
            expiry = date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            if expiry >= date.today():
                score += 20
                reasons.append(f"订阅在有效期内(+20): 至 {valid_until}")
        except ValueError:
            pass

    if not reasons:
        reasons.append("无有效会员证明，回落普通通道")

    manual_review = bool(re.search(r"手工解析|手动截图|人工复核", str(proof.get("note") or "")))
    if manual_review and score >= 60:
        reasons.append("人工兜底证明，转人工复核")
    decision = "fast_pass" if score >= 60 and not manual_review else ("fast_review" if score >= 40 else "standard")
    print(json.dumps({"score": score, "decision": decision, "reasons": reasons}, ensure_ascii=False))


if __name__ == "__main__":
    main()
