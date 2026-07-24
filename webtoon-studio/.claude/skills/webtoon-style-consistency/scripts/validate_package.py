#!/usr/bin/env python3
"""웹툰 에피소드 산출물 정합성 검증.

패널 레이아웃 / 대사 스크립트 / 캐릭터 시트의 경계면을 교차 대조한다.
에이전트별로 나뉘어 생성된 산출물은 각자 내부적으로는 완결돼 보여도
서로를 참조하는 ID에서 깨지는 경우가 가장 흔하므로, 리뷰 라운드 전에 돌린다.

종료 코드: 0 = 통과, 1 = MAJOR만 존재, 2 = BLOCKER 존재
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

NARRATOR_SPEAKERS = {"내레이션", "narration", "나레이션", "-", ""}
NON_SPEAKER_TYPES = {"narration", "sfx", "caption"}

DEFAULT_MAX_BUBBLES = 4
DEFAULT_MAX_PANEL_CHARS = 120
DEFAULT_MAX_SLOT_CHARS = 40
MIN_PANEL_HEIGHT = 180
MAX_PANEL_HEIGHT = 2600


class Findings:
    def __init__(self) -> None:
        self.items: list[tuple[str, str, str]] = []  # (severity, location, message)

    def add(self, severity: str, location: str, message: str) -> None:
        self.items.append((severity, location, message))

    def count(self, severity: str) -> int:
        return sum(1 for s, _, _ in self.items if s == severity)


def load_json(path: Path, findings: Findings, label: str) -> dict | None:
    if not path.exists():
        findings.add("BLOCKER", str(path), f"{label} 파일이 없다")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        findings.add("BLOCKER", str(path), f"{label} JSON 파싱 실패: {exc}")
        return None


def check_panels(panels_doc: dict, findings: Findings) -> dict:
    """패널 문서 내부 무결성을 검사하고 {panel_id: panel} 인덱스를 돌려준다."""
    panels = panels_doc.get("panels")
    if not isinstance(panels, list) or not panels:
        findings.add("BLOCKER", "panels", "panels 배열이 비었거나 배열이 아니다")
        return {}

    index: dict[str, dict] = {}
    seen_slots: dict[str, str] = {}
    for pos, panel in enumerate(panels):
        pid = panel.get("id")
        loc = pid or f"panels[{pos}]"
        if not pid:
            findings.add("BLOCKER", loc, "패널에 id가 없다")
            continue
        if pid in index:
            findings.add("BLOCKER", pid, "패널 id가 중복됐다")
            continue
        index[pid] = panel

        height = panel.get("height")
        if not isinstance(height, (int, float)):
            findings.add("BLOCKER", pid, "height가 숫자가 아니다")
        elif not (MIN_PANEL_HEIGHT <= height <= MAX_PANEL_HEIGHT):
            findings.add(
                "MAJOR", pid,
                f"height {height}px가 허용 범위({MIN_PANEL_HEIGHT}~{MAX_PANEL_HEIGHT})를 벗어난다",
            )

        for slot in panel.get("bubble_slots") or []:
            sid = slot.get("id")
            if not sid:
                findings.add("BLOCKER", pid, "말풍선 슬롯에 id가 없다")
                continue
            if sid in seen_slots:
                findings.add("BLOCKER", sid, f"슬롯 id가 {seen_slots[sid]}와 중복됐다")
                continue
            seen_slots[sid] = pid
            if not sid.startswith(f"{pid}-"):
                findings.add("MAJOR", sid, f"슬롯 id가 소속 패널 {pid} 접두사를 따르지 않는다")
    return index


def check_dialogue(
    dialogue_doc: dict,
    panel_index: dict[str, dict],
    findings: Findings,
    max_bubbles: int,
    max_panel_chars: int,
    default_max_chars: int,
) -> set[str]:
    """대사 ↔ 패널 참조를 대조하고, 대사가 채운 슬롯 id 집합을 돌려준다."""
    lines = dialogue_doc.get("lines")
    if not isinstance(lines, list):
        findings.add("BLOCKER", "lines", "lines 배열이 없다")
        return set()

    filled: set[str] = set()
    per_panel_chars: dict[str, int] = {}
    per_panel_count: dict[str, int] = {}

    for pos, line in enumerate(lines):
        sid = line.get("slot_id")
        loc = sid or f"lines[{pos}]"
        if not sid:
            findings.add("BLOCKER", loc, "대사에 slot_id가 없다")
            continue
        if sid in filled:
            findings.add("BLOCKER", sid, "같은 슬롯에 대사가 두 번 배정됐다")
            continue

        pid = line.get("panel_id") or sid.rsplit("-", 1)[0]
        panel = panel_index.get(pid)
        if panel is None:
            findings.add("BLOCKER", sid, f"존재하지 않는 패널 {pid}을 참조한다")
            continue

        slots = {s.get("id"): s for s in (panel.get("bubble_slots") or [])}
        slot = slots.get(sid)
        if slot is None:
            findings.add("BLOCKER", sid, f"패널 {pid}이 선언하지 않은 슬롯이다")
            continue

        filled.add(sid)
        text = line.get("text") or ""
        if not text.strip():
            findings.add("BLOCKER", sid, "대사 텍스트가 비었다")

        declared = line.get("char_count")
        actual = len(text)
        if isinstance(declared, int) and declared != actual:
            findings.add("MAJOR", sid, f"char_count {declared}가 실제 길이 {actual}와 다르다")

        limit = slot.get("max_chars") or default_max_chars
        if actual > limit:
            findings.add("MAJOR", sid, f"{actual}자로 슬롯 한계 {limit}자를 넘는다")

        slot_type = slot.get("type")
        line_type = line.get("type")
        if slot_type and line_type and slot_type != line_type:
            findings.add("MAJOR", sid, f"슬롯 타입 {slot_type}와 대사 타입 {line_type}가 다르다")

        per_panel_chars[pid] = per_panel_chars.get(pid, 0) + actual
        per_panel_count[pid] = per_panel_count.get(pid, 0) + 1

    for pid, count in per_panel_count.items():
        if count > max_bubbles:
            findings.add("MAJOR", pid, f"말풍선 {count}개로 한계 {max_bubbles}개를 넘는다")
    for pid, chars in per_panel_chars.items():
        if chars > max_panel_chars:
            findings.add("MAJOR", pid, f"패널 총 {chars}자로 한계 {max_panel_chars}자를 넘는다")

    return filled


def check_empty_slots(panel_index: dict[str, dict], filled: set[str], findings: Findings) -> None:
    for pid, panel in panel_index.items():
        for slot in panel.get("bubble_slots") or []:
            sid = slot.get("id")
            if sid and sid not in filled:
                findings.add("BLOCKER", sid, f"패널 {pid}이 선언한 슬롯에 대사가 없다")


def check_characters(
    characters_doc: dict,
    panel_index: dict[str, dict],
    dialogue_doc: dict,
    findings: Findings,
) -> None:
    roster = characters_doc.get("characters")
    if not isinstance(roster, list) or not roster:
        findings.add("BLOCKER", "characters", "characters 배열이 비었다")
        return

    names: set[str] = set()
    for pos, char in enumerate(roster):
        name = char.get("name")
        if not name:
            findings.add("BLOCKER", f"characters[{pos}]", "캐릭터에 name이 없다")
            continue
        if name in names:
            findings.add("BLOCKER", name, "캐릭터 이름이 중복됐다")
        names.add(name)
        if not (char.get("anchor_prompt") or "").strip():
            findings.add("MAJOR", name, "anchor_prompt가 비었다 — 회차 간 외형 일관성의 근거가 없다")

    for pid, panel in panel_index.items():
        for name in panel.get("characters") or []:
            if name not in names:
                findings.add("BLOCKER", pid, f"캐릭터 시트에 없는 인물 '{name}'이 등장한다")

    for line in dialogue_doc.get("lines") or []:
        speaker = (line.get("speaker") or "").strip()
        if line.get("type") in NON_SPEAKER_TYPES or speaker in NARRATOR_SPEAKERS:
            continue
        if speaker not in names:
            findings.add("BLOCKER", line.get("slot_id", "?"), f"캐릭터 시트에 없는 화자 '{speaker}'")


def report(findings: Findings, as_json: bool) -> int:
    blockers = findings.count("BLOCKER")
    majors = findings.count("MAJOR")

    if as_json:
        payload = {
            "findings": [
                {"severity": s, "location": loc, "message": msg} for s, loc, msg in findings.items
            ],
            "summary": {"blocker": blockers, "major": majors, "total": len(findings.items)},
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if not findings.items:
            print("PASS — 정합성 위반 없음")
        else:
            order = {"BLOCKER": 0, "MAJOR": 1}
            for sev, loc, msg in sorted(findings.items, key=lambda f: (order.get(f[0], 9), f[1])):
                print(f"[{sev}] {loc}: {msg}")
            print(f"\n요약: BLOCKER {blockers} / MAJOR {majors} / 합계 {len(findings.items)}")

    if blockers:
        return 2
    if majors:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="웹툰 에피소드 산출물 정합성 검증")
    parser.add_argument("--panels", required=True, type=Path)
    parser.add_argument("--dialogue", required=True, type=Path)
    parser.add_argument("--characters", type=Path, help="생략 가능. 주면 인물 참조까지 대조한다")
    parser.add_argument("--max-bubbles", type=int, default=DEFAULT_MAX_BUBBLES)
    parser.add_argument("--max-panel-chars", type=int, default=DEFAULT_MAX_PANEL_CHARS)
    parser.add_argument("--max-slot-chars", type=int, default=DEFAULT_MAX_SLOT_CHARS)
    parser.add_argument("--json", action="store_true", help="JSON으로 출력")
    args = parser.parse_args()

    findings = Findings()
    panels_doc = load_json(args.panels, findings, "패널 레이아웃")
    dialogue_doc = load_json(args.dialogue, findings, "대사 스크립트")
    if panels_doc is None or dialogue_doc is None:
        return report(findings, args.json)

    panel_index = check_panels(panels_doc, findings)
    filled = check_dialogue(
        dialogue_doc, panel_index, findings,
        args.max_bubbles, args.max_panel_chars, args.max_slot_chars,
    )
    check_empty_slots(panel_index, filled, findings)

    if args.characters:
        characters_doc = load_json(args.characters, findings, "캐릭터 시트")
        if characters_doc is not None:
            check_characters(characters_doc, panel_index, dialogue_doc, findings)

    return report(findings, args.json)


if __name__ == "__main__":
    sys.exit(main())
