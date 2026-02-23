---
description: UE5 레벨 내 액터 조회/검색/삭제/트랜스폼 설정
allowed-tools: Bash(curl:*)
argument-hint: <action> [args...] (예: list, find Wall*, delete MyActor)
---

UE5 레벨 내 액터 작업을 수행해라. HTTP 서버(localhost:8080)에 Python 스크립트를 전송하여 실행한다.

## 사용 가능한 함수 (skills.actor_ops)

- `get_actors_in_level()` — 모든 액터 목록
- `find_actors_by_name(pattern)` — 이름 패턴 검색
- `delete_actor(name)` — 액터 삭제
- `set_actor_transform(name, location=None, rotation=None, scale=None)` — 트랜스폼 설정

## 호출 방법

Bash로 curl을 사용하여 POST /execute 엔드포인트를 호출해라:

```bash
curl -s -X POST http://127.0.0.1:8080/execute -H "Content-Type: application/json" -d "{\"mode\":\"editor\",\"script\":\"from skills.actor_ops import get_actors_in_level\\nresult['actors'] = get_actors_in_level()\",\"params\":{}}"
```

사용자 요청: $ARGUMENTS
