# 산출물 데이터 계약 (Data Contract)

에이전트 간 경계면 스키마. panel-planner가 정의하고 dialogue-editor가 채우며, style-guardian이 `validate_package.py`로 대조한다.

## 목차

1. [04_panel_layout.json](#1-04_panel_layoutjson)
2. [05_dialogue_script.json](#2-05_dialogue_scriptjson)
3. [03_character_sheet.json](#3-03_character_sheetjson)
4. [ID 규칙](#4-id-규칙)
5. [열거값](#5-열거값)

---

## 1. `04_panel_layout.json`

```json
{
  "episode": { "series": "새벽의 관측자", "number": 3, "title": "지붕 위의 신호" },
  "canvas": { "width": 800, "gutter_default": 40 },
  "panels": [
    {
      "id": "P01",
      "height": 1100,
      "gutter_after": 120,
      "beat": "B01",
      "shot": "establishing",
      "angle": "bird",
      "description": "새벽 4시 낡은 아파트 단지 전경. 옥상에 홀로 선 시우의 실루엣.",
      "characters": ["시우"],
      "focus": "옥상 난간 위 실루엣",
      "bubble_slots": [
        {
          "id": "P01-B1",
          "type": "narration",
          "speaker": "내레이션",
          "max_chars": 40,
          "anchor": { "x": 0.5, "y": 0.12 }
        }
      ],
      "sfx": [{ "text": "삐-", "anchor": { "x": 0.72, "y": 0.4 }, "scale": "medium" }],
      "transition": "scroll-reveal",
      "notes": "가로등 색온도는 SB-COLOR-04"
    }
  ]
}
```

| 필드 | 필수 | 의미 |
|------|------|------|
| `height` | ✅ | 컷 높이(px). `canvas.width` 기준. 180~2600 범위를 벗어나면 MAJOR |
| `gutter_after` | | 다음 컷까지 여백. 생략 시 `canvas.gutter_default`. 여백은 독자의 호흡이므로 리듬 설계의 일부다 |
| `beat` | ✅ | 스토리 비트시트의 비트 ID. 이 연결이 없으면 서사 누락 검수가 불가능하다 |
| `characters` | ✅ | 등장 인물 **이름** 배열. 캐릭터 시트의 `name`과 정확히 일치해야 한다 |
| `bubble_slots` | | 말풍선 **자리**만 선언한다. 대사 텍스트는 dialogue-editor의 몫 |
| `focus` | | 시선 유도 지점. 세로 스크롤은 시선이 위→아래 단방향이라 컷마다 착지점이 필요하다 |

**`bubble_slots`는 자리이고 대사가 아니다.** panel-planner가 텍스트까지 쓰면 dialogue-editor의 산출물과 이중 정본이 생겨 어느 쪽이 최신인지 알 수 없게 된다. panel-planner는 `max_chars`로 **공간 예산**만 통보한다.

## 2. `05_dialogue_script.json`

```json
{
  "episode": { "series": "새벽의 관측자", "number": 3 },
  "lines": [
    {
      "slot_id": "P01-B1",
      "panel_id": "P01",
      "speaker": "내레이션",
      "type": "narration",
      "text": "그 신호는 언제나 새벽 4시에 왔다.",
      "char_count": 20,
      "note": "SB-TEXT-02 내레이션 과거형 유지"
    }
  ]
}
```

`slot_id`는 패널이 선언한 슬롯과 1:1이다. 선언되지 않은 슬롯에 대사를 쓰거나, 선언된 슬롯을 비우면 둘 다 `BLOCKER`다 — 전자는 작화가가 그릴 자리가 없고, 후자는 빈 말풍선이 남는다.

`char_count`는 `len(text)`와 일치해야 한다. 불일치는 대사를 고치고 카운트를 갱신하지 않은 흔적이라, 다른 곳도 갱신이 안 됐을 신호다.

## 3. `03_character_sheet.json`

```json
{
  "series": "새벽의 관측자",
  "characters": [
    {
      "id": "CH01",
      "name": "시우",
      "role": "주인공",
      "anchor_rule": "SB-CHAR-01",
      "anchor_prompt": "dark navy bob haircut, mole under left eye, slim 7.5-head figure, grey scarf",
      "outfits": [{ "id": "OF01", "name": "교복", "prompt": "navy blazer, loose red tie" }],
      "expressions": [{ "id": "EX01", "name": "경계", "prompt": "narrowed eyes, tight jaw" }],
      "prompts": {
        "base": "...",
        "sheet": "character reference sheet, front/side/back, T-pose",
        "negative": "extra fingers, inconsistent hair length, altered eye color"
      }
    }
  ]
}
```

`anchor_prompt`는 **모든 생성 프롬프트에 그대로 삽입되는 불변 문자열**이다. 회차마다 표현을 바꾸면 같은 인물로 보이지 않으므로, 문구를 다듬고 싶어도 바이블 개정 없이는 손대지 않는다.

## 4. ID 규칙

| 대상 | 형식 | 예 |
|------|------|-----|
| 패널 | `P` + 2자리 0패딩 | `P01`, `P17` |
| 말풍선 슬롯 | `{패널ID}-B{n}` | `P03-B2` |
| 비트 | `B` + 2자리 | `B04` |
| 캐릭터 | `CH` + 2자리 | `CH01` |

슬롯 ID에 패널 ID 접두사를 강제하는 이유는, 대사 스크립트만 봐도 어느 컷인지 즉시 알 수 있어야 하기 때문이다. 접두사 위반은 MAJOR.

패널 번호는 **스크롤 순서**와 일치시킨다. 중간에 컷을 삽입할 때는 전체 재번호 대신 `P07A` 같은 삽입 번호를 쓰고, 회차 확정 시 한 번에 재번호한다 — 중간 재번호는 대사 스크립트의 모든 `slot_id`를 동시에 깨뜨린다.

## 5. 열거값

**`shot`**: `establishing` · `wide` · `medium` · `closeup` · `extreme-closeup` · `insert` · `bird` · `worm`
**`angle`**: `eye` · `high` · `low` · `dutch` · `over-shoulder` · `pov`
**`transition`**: `cut` (즉시 전환) · `scroll-reveal` (긴 여백으로 서서히 드러냄) · `beat-gap` (침묵의 여백) · `match-cut` (형태 연결) · `time-skip`
**`bubble_slots[].type`**: `normal` · `thought` · `shout` · `whisper` · `narration` · `caption`
**`sfx[].scale`**: `small` · `medium` · `large` · `huge`

열거값 외의 문자열을 쓰면 콘티 렌더러가 기본 스타일로 떨어진다(오류는 아니다). 새 값이 필요하면 바이블에 신규 규칙으로 등록한 뒤 사용한다.
