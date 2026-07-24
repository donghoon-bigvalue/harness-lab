#!/usr/bin/env python3
"""패널 레이아웃 JSON을 세로 스크롤 콘티(썸네일 목업)로 렌더링한다.

패널 높이·간격·말풍선 위치는 숫자로만 보면 검수가 불가능하다. 실제 비율대로
쌓아 봐야 스크롤 리듬이 끊기는 지점, 말풍선이 겹치는 지점, 컷이 화면을 넘치는
지점이 드러난다. 그래서 리뷰 라운드 입력으로 이 목업을 함께 낸다.

출력: 단일 HTML(인라인 SVG). 외부 리소스를 쓰지 않으므로 그대로 열람·공유 가능.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

SHOT_TINT = {
    "extreme-closeup": "#f3c9c0",
    "closeup": "#f6ddc9",
    "medium": "#e6e2d3",
    "wide": "#d6e2e6",
    "establishing": "#cdd8ea",
    "bird": "#dcd6ea",
    "worm": "#e4d3dd",
    "insert": "#e9e9e9",
}
BUBBLE_STYLE = {
    "normal": ("#ffffff", "#222222", "solid"),
    "thought": ("#fbfbff", "#4a4a6a", "dashed"),
    "shout": ("#fff6f0", "#a02c14", "solid"),
    "whisper": ("#f7f7f7", "#666666", "dotted"),
    "narration": ("#1f1f1f", "#f4f4f4", "solid"),
    "caption": ("#efe9d8", "#3a3226", "solid"),
}


def wrap(text: str, per_line: int, max_lines: int) -> list[str]:
    """CJK 혼용 텍스트를 글자 수 기준으로 접는다.

    SVG에는 자동 줄바꿈이 없어 직접 접어야 한다. 한글은 폭이 균일해
    글자 수 기준 근사가 실사용에서 충분히 맞는다.
    """
    text = " ".join(text.split())
    lines: list[str] = []
    while text and len(lines) < max_lines:
        if len(text) <= per_line:
            lines.append(text)
            break
        cut = text.rfind(" ", 0, per_line + 1)
        if cut <= per_line // 2:
            cut = per_line
        lines.append(text[:cut].rstrip())
        text = text[cut:].lstrip()
    if text and len(lines) == max_lines:
        lines[-1] = lines[-1][: max(0, per_line - 1)] + "…"
    return lines


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def svg_text(x: float, y: float, lines: list[str], size: float, fill: str,
             anchor: str = "start", weight: str = "normal", line_height: float = 1.35) -> str:
    out = []
    for i, line in enumerate(lines):
        out.append(
            f'<text x="{x:.1f}" y="{y + i * size * line_height:.1f}" font-size="{size:.1f}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{esc(line)}</text>'
        )
    return "".join(out)


def render_bubble(slot: dict, text: str, pw: float, ph: float) -> str:
    anchor = slot.get("anchor") or {}
    cx = float(anchor.get("x", 0.5)) * pw
    cy = float(anchor.get("y", 0.2)) * ph
    btype = slot.get("type", "normal")
    fill, ink, dash = BUBBLE_STYLE.get(btype, BUBBLE_STYLE["normal"])
    stroke_dash = {"dashed": "8 6", "dotted": "2 5"}.get(dash, "")

    body = text or f'({slot.get("speaker") or btype})'
    per_line = 11
    lines = wrap(body, per_line, 4)
    rw = min(pw * 0.62, max(96.0, per_line * 11.0))
    rh = 20 + len(lines) * 17
    rx, ry = cx - rw / 2, cy - rh / 2
    rx = max(8.0, min(rx, pw - rw - 8))
    ry = max(8.0, min(ry, ph - rh - 8))

    shape = (
        f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{rw:.1f}" height="{rh:.1f}" rx="{10 if btype != "shout" else 3}" '
        f'fill="{fill}" stroke="{ink}" stroke-width="1.6"'
        + (f' stroke-dasharray="{stroke_dash}"' if stroke_dash else "")
        + "/>"
    )
    speaker = slot.get("speaker") or ""
    tag = (
        svg_text(rx + 6, ry - 5, [f"{slot.get('id','')} {speaker}".strip()], 9, "#8a8a8a")
        if slot.get("id") else ""
    )
    return shape + tag + svg_text(rx + rw / 2, ry + 20, lines, 12, ink, anchor="middle")


def render_panel(panel: dict, texts: dict[str, str], width: float) -> str:
    ph = float(panel.get("height", 600))
    pid = panel.get("id", "?")
    shot = panel.get("shot", "medium")
    tint = SHOT_TINT.get(shot, "#e8e8e8")

    parts = [
        f'<rect x="0" y="0" width="{width:.1f}" height="{ph:.1f}" fill="{tint}" stroke="#33312e" stroke-width="2"/>'
    ]
    header = f'{pid} · {shot}'
    if panel.get("angle"):
        header += f' · {panel["angle"]}'
    parts.append(
        f'<rect x="0" y="0" width="{min(width, 8.0 * len(header) + 20):.1f}" height="22" fill="#33312e"/>'
    )
    parts.append(svg_text(8, 15.5, [header], 11.5, "#f5f2ec", weight="bold"))

    if panel.get("beat"):
        parts.append(svg_text(width - 8, 15.5, [f'beat {panel["beat"]}'], 10, "#5c5750", anchor="end"))

    desc = panel.get("description") or panel.get("scene") or ""
    if desc:
        parts.append(svg_text(10, 42, wrap(desc, int(width / 7.2), 5), 12, "#3a352f"))

    cast = panel.get("characters") or []
    if cast:
        parts.append(svg_text(10, ph - 26, [" / ".join(str(c) for c in cast)], 11, "#4a453e"))
    if panel.get("transition"):
        parts.append(svg_text(width - 8, ph - 26, [f'→ {panel["transition"]}'], 10, "#6b655c", anchor="end"))
    if panel.get("notes"):
        parts.append(svg_text(10, ph - 10, wrap(str(panel["notes"]), int(width / 6.4), 1), 10, "#7a736a"))

    for sfx in panel.get("sfx") or []:
        a = sfx.get("anchor") or {}
        size = {"small": 16, "medium": 24, "large": 38, "huge": 54}.get(sfx.get("scale", "medium"), 24)
        parts.append(
            svg_text(float(a.get("x", 0.5)) * width, float(a.get("y", 0.6)) * ph,
                     [str(sfx.get("text", ""))], size, "#b6482d", anchor="middle", weight="bold")
        )

    for slot in panel.get("bubble_slots") or []:
        parts.append(render_bubble(slot, texts.get(slot.get("id", ""), ""), width, ph))

    return "".join(parts)


def build(panels_doc: dict, dialogue_doc: dict | None, scale: float) -> str:
    canvas = panels_doc.get("canvas") or {}
    width = float(canvas.get("width", 800))
    default_gutter = float(canvas.get("gutter_default", 40))
    panels = panels_doc.get("panels") or []

    texts: dict[str, str] = {}
    if dialogue_doc:
        for line in dialogue_doc.get("lines") or []:
            if line.get("slot_id"):
                texts[line["slot_id"]] = line.get("text", "")

    body, y, total_h = [], 0.0, 0.0
    for panel in panels:
        h = float(panel.get("height", 600))
        body.append(f'<g transform="translate(0,{y:.1f})">{render_panel(panel, texts, width)}</g>')
        gutter = float(panel.get("gutter_after", default_gutter))
        y += h + gutter
        total_h = y
    total_h = max(total_h, 1.0)

    ep = panels_doc.get("episode") or {}
    title = f'{ep.get("series", "webtoon")} {ep.get("number", "")}화 — {ep.get("title", "")}'.strip()
    bubble_count = sum(len(p.get("bubble_slots") or []) for p in panels)
    stats = (
        f'컷 {len(panels)} · 말풍선 {bubble_count} · 총 높이 {int(total_h)}px '
        f'· 평균 컷 높이 {int(sum(float(p.get("height", 600)) for p in panels) / max(1, len(panels)))}px'
    )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {total_h:.0f}" '
        f'width="{width * scale:.0f}" style="font-family:system-ui,-apple-system,\'Noto Sans KR\',sans-serif">'
        f'<rect width="{width:.0f}" height="{total_h:.0f}" fill="#faf8f4"/>{"".join(body)}</svg>'
    )

    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>콘티 — {esc(title)}</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ margin:0; padding:24px 12px 64px; background:#20201e; color:#efece6;
         font-family:system-ui,-apple-system,'Noto Sans KR',sans-serif; }}
  header {{ max-width:960px; margin:0 auto 20px; }}
  h1 {{ font-size:18px; margin:0 0 6px; }}
  p {{ margin:0; font-size:13px; color:#a9a49b; }}
  .stage {{ display:flex; justify-content:center; }}
  svg {{ max-width:100%; height:auto; box-shadow:0 0 0 1px #3a3833, 0 12px 40px rgba(0,0,0,.45); }}
</style></head>
<body>
<header><h1>{esc(title)}</h1><p>{esc(stats)}</p></header>
<div class="stage">{svg}</div>
</body></html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="패널 레이아웃 JSON → 세로 스크롤 콘티 HTML")
    parser.add_argument("--panels", required=True, type=Path)
    parser.add_argument("--dialogue", type=Path, help="주면 말풍선에 실제 대사를 채운다")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--scale", type=float, default=0.75, help="표시 배율 (기본 0.75)")
    args = parser.parse_args()

    try:
        panels_doc = json.loads(args.panels.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"패널 레이아웃을 읽을 수 없다: {exc}", file=sys.stderr)
        return 2

    dialogue_doc = None
    if args.dialogue:
        try:
            dialogue_doc = json.loads(args.dialogue.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            # 대사는 선택 입력이다. 없으면 슬롯 자리만 그리고 계속 진행한다.
            print(f"대사 스크립트를 건너뛴다: {exc}", file=sys.stderr)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build(panels_doc, dialogue_doc, args.scale), encoding="utf-8")
    print(f"콘티 생성: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
