# ue - UE5 에디터 제어 스킬

Unreal Engine 5 에디터를 Claude Code에서 Python 스크립트로 원격 제어하는 스킬셋.

## 커맨드

| 커맨드 | 설명 |
|--------|------|
| `/ue:actor` | 레벨 내 액터 조작 |
| `/ue:blueprint` | Blueprint 생성/수정 |
| `/ue:function` | Blueprint 함수 관리 |
| `/ue:graph` | Blueprint 그래프 노드 조작 |
| `/ue:material` | 머티리얼 작업 |
| `/ue:pie` | PIE 모드 제어/스크린샷 |
| `/ue:spawn` | 물리 액터 스폰 |
| `/ue:structure` | 구조물 생성 |
| `/ue:variable` | Blueprint 변수 관리 |

## 아키텍처

```
Claude Code → curl (HTTP POST) → Python HTTP Server (localhost:8080) → UE5 Editor Python API
```

1. UE5 에디터 내에서 `init_unreal.py`가 HTTP 서버를 실행 (port 8080)
2. Claude Code가 `/ue:*` 커맨드로 Python 코드를 HTTP POST로 전송
3. 서버가 코드를 `exec()`로 실행하고 결과를 반환

## 설치

### 1. UE5 프로젝트에 Python 파일 복사

```powershell
# 서버 스크립트
Copy-Item "ue\server\init_unreal.py" "<UE프로젝트>\Content\Python\"

# 스킬 모듈
Copy-Item -Recurse "ue\skills" "<UE프로젝트>\Content\Python\skills"
```

### 2. UE5 에디터 설정

1. Edit > Project Settings > Plugins > Python
2. "Startup Scripts"에 `init_unreal.py` 추가
3. 에디터 재시작

### 3. Claude Code에 커맨드 등록

```powershell
# 심볼릭 링크
New-Item -ItemType Junction -Path ".claude\commands\ue" -Target "D:\Rust\claude-skills\ue\.claude\commands\ue"
```

## 의존성

- **Unreal Engine 5** (5.3+, Python 플러그인 활성화)
- **curl** (HTTP POST 전송용)

## 스킬 모듈 구조

```
skills/
├── __init__.py
├── actor_ops.py          # 액터 생성/이동/삭제
├── blueprint_core.py     # BP 생성/컴파일
├── blueprint_read.py     # BP 구조 읽기
├── blueprint_graph.py    # BP 그래프 노드 조작
├── editor_ops.py         # 에디터 유틸리티
├── material_ops.py       # 머티리얼 생성/편집
├── physics_actor.py      # 물리 액터 스폰
└── structures/           # 구조물 생성 프리셋
    ├── primitives.py
    ├── buildings.py
    ├── engineering.py
    └── complex.py
```
