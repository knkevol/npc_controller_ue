---
description: UE5 PIE(Play In Editor) 모드 제어 및 스크린샷
allowed-tools: Bash(curl:*)
argument-hint: <action> [options...] (예: start, stop, status, screenshot test.png 1920x1080)
---

PIE 모드를 제어하고 스크린샷을 촬영해라.

## 사용 가능한 함수 (skills.editor_ops)

- `start_pie()` — PIE 시작
- `stop_pie()` — PIE 종료
- `is_pie_active()` — PIE 상태 확인
- `simulate_pie()` — Simulate 모드 시작
- `take_screenshot(filename="screenshot.png", res_x=1920, res_y=1080)` — 고해상도 스크린샷
- `take_screenshot_console(resolution="1920x1080")` — 콘솔 스크린샷
- `get_screenshot_dir()` — 스크린샷 디렉토리 확인

## 호출 예시

```bash
# PIE 시작
curl -s -X POST http://127.0.0.1:8080/execute -H "Content-Type: application/json" -d "{\"mode\":\"editor\",\"script\":\"from skills.editor_ops import start_pie\\nresult.update(start_pie())\",\"params\":{}}"

# 스크린샷
curl -s -X POST http://127.0.0.1:8080/execute -H "Content-Type: application/json" -d "{\"mode\":\"editor\",\"script\":\"from skills.editor_ops import take_screenshot\\nresult.update(take_screenshot('test.png', 1920, 1080))\",\"params\":{}}"
```

사용자 요청: $ARGUMENTS
