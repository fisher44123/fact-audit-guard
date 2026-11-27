#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Zero-dependency pre-publish deterministic fact & risk auditor."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

RULES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rules.json")
_SKIP_NUM_CTX = re.compile(
    r"(\d{2}:\d{2}|\d{4}-\d{2}-\d{2}|https?://|file:///|\bv?\d+\.\d+\.\d+|L\d+|#\d+|\.md|\.json|\.py)"
)
_ENUM_ORDINAL_RE = re.compile(r"第一(?:步|条|轮|阶段|部分|层|版|次|个|篇|点|天|周|名|手|时间)")


def load_rules(path: str | None = None) -> dict:
    with open(path or RULES_FILE, encoding="utf-8") as f:
        return json.load(f)


def _check_numbers(text: str, rules: dict) -> tuple[int, list[tuple[int, str, str]]]:
    nc = rules["number_check"]
    units = "|".join(re.escape(u) for u in nc["stat_units"])
    stat = re.compile(r"\d[\d,\.]*\s*(%s)" % units)
    prefixes = tuple(nc["skip_line_prefix"])
    design = re.compile("|".join(nc["design_param_words"]))
    src = re.compile(rules["source_hint"])
    bad, total = [], 0
    lines = text.splitlines()
    for idx, ln in enumerate(lines):
        st = ln.strip()
        if st.startswith(prefixes) or not stat.search(ln):
            continue
        scope = "\n".join(lines[max(0, idx - 1): min(len(lines), idx + 2)])
        for m in stat.finditer(ln):
            raw = m.group(0)
            if re.match(r"^\d{1,2}\.\s", raw):
                continue
            num = re.match(r"[\d,\.]+", raw).group(0)
            if len(num.replace(",", "")) < 2:
                continue
            ctx = ln[max(0, m.start() - 80): m.end() + 80]
            if _SKIP_NUM_CTX.search(ctx) or design.search(ctx):
                continue
            total += 1
            if not (src.search(ctx) or src.search(scope)):
                bad.append((idx + 1, num, st[:60]))
    return total, bad


def _check_word_list(text: str, words: list[str], neg_pat: str, src_re: re.Pattern, *, strip_ord: bool = False) -> list[str]:
    neg = re.compile(neg_pat)
    hits = []
    for para in re.split(r"\n\s*\n", text):
        st = para.lstrip()
        if not st or st.startswith(("#", "```", ">")):
            continue
        body = _ENUM_ORDINAL_RE.sub("", para) if strip_ord else para
        found = [w for w in words if w in body]
        if not found or neg.search(para):
            continue
        if len(src_re.findall(para)) < 2 and len(st) > 20:
            hits.append("「%s」" % " ".join(found))
    return hits


def _check_claims(text: str, rules: dict, src_re: re.Pattern) -> list[str]:
    neg = re.compile(rules["claim_negation"])
    bad = []
    for pat, label in rules["claim_patterns"]:
        for m in re.finditer(pat, text):
            near = text[max(0, m.start() - 120): m.end() + 120]
            if not (src_re.search(near) or neg.search(near)):
                bad.append(label)
    return bad


def run_audit(text: str, rules: dict) -> tuple[int, int, list[tuple[str, str, bool, str]]]:
    src_re = re.compile(rules["source_hint"])
    fail_on = set(rules["fail_on"])
    total, bad_nums = _check_numbers(text, rules)
    thr = float(rules["number_check"]["max_unsourced_ratio"])
    ratio = (len(bad_nums) / total) if total else 0.0

    claims = _check_claims(text, rules, src_re)
    over = _check_word_list(text, rules["overclaim_words"], rules["negation_words"], src_re)
    sup = _check_word_list(text, rules["superlative_words"], rules["negation_words"], src_re, strip_ord=True)
    gap_ok = bool(re.search(rules["gap_section_pattern"], text))
    rev_cnt = len(re.findall(rules["reverse_question_pattern"], text, re.M))
    need_rev = int(rules["min_reverse_questions"])

    checks = [
        ("numbers", "统计数字带出处", ratio <= thr,
         f"{total} 个统计量中 {len(bad_nums)} 个无出处（{ratio:.0%}）" + (f"；如 L{bad_nums[0][0]}「{bad_nums[0][1]}」" if bad_nums else "")),
        ("claims", "无裸露自证断言", not claims, "通过" if not claims else "；".join(claims[:3])),
        ("overclaim", "越级词 ≥2 处来源", not over, "通过" if not over else "；".join(over[:3])),
        ("superlatives", "最高级词汇合规", not sup, "通过" if not sup else "；".join(sup[:3])),
        ("gap_section", "覆盖边界/Open Questions", gap_ok, "已声明" if gap_ok else "缺失局限或 Open Questions 章节"),
        ("reverse", f"反向质疑 ≥{need_rev} 条", rev_cnt >= need_rev, f"当前 {rev_cnt} 条"),
    ]
    blocks = sum(1 for k, _, ok, _ in checks if not ok and k in fail_on)
    fixes = sum(1 for k, _, ok, _ in checks if not ok and k not in fail_on)
    return blocks, fixes, checks


def main() -> int:
    ap = argparse.ArgumentParser(description="Fact Audit Guard pre-publish checker")
    ap.add_argument("draft", help="Markdown draft path")
    ap.add_argument("--rules", help="Custom rules JSON path")
    ap.add_argument("--strict", action="store_true", help="Exit 1 when any [BLOCK] exists")
    args = ap.parse_args()

    if not os.path.exists(args.draft):
        print(f"File not found: {args.draft}", file=sys.stderr)
        return 2
    text = open(args.draft, encoding="utf-8").read()
    rules = load_rules(args.rules)
    fail_on = set(rules["fail_on"])
    blocks, fixes, checks = run_audit(text, rules)

    print("=== Fact Audit Guard ===")
    for key, label, ok, detail in checks:
        if ok:
            tag = "[PASS]"
        elif key in fail_on:
            tag = "[BLOCK]"
        elif key in ("overclaim", "superlatives", "gap_section"):
            tag = "[FIX]"
        else:
            tag = "[NOTE]"
        print(f"  {tag:<7} {label}: {detail}")
    print(f"Summary: BLOCK={blocks}, FIX/NOTE={fixes}")
    return 1 if (args.strict and blocks > 0) else 0


if __name__ == "__main__":
    sys.exit(main())
