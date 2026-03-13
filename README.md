# 🚶 *모바일 ↔ Unreal Engine 통신 AI NPC Controller_UE*
UE5와 Flutter를 기반으로 모바일 ↔ Unreal Engine을 FAST API 서버를 통해 통신하여 엔진의 에디터를 조작하는 프로젝트입니다.
<br />

<br />
<br />

***

### ✅ 주요 기능

-  **LLM 중심의 이종 플랫폼 통합 파이프라인 (Flutter ↔ LLM ↔ Unreal Engine)**
    - Flutter 앱에서 자연어 명령을 입력하면 FastAPI 서버를 거쳐 언리얼 엔진 NPC에 즉각 반영되는 단방향 제어 파이프라인 구현
    - HTTP(REST API) 기반 통신으로 각 플랫폼 간 명령 전달 및 응답 처리
      
      <br />
- **MCP(Model Context Protocol) 기반의 지능형 판단 레이어**
    - 사용자가 입력한 자연어 명령을 LLM이 분석하여 언리얼 엔진이 즉각 실행할 수 있도록 정형화된 JSON 포맷(예: action: MOVE, target: Cube)으로 변환하여 전달

      <br />
- **Vibe Coding(ClaudeCode)을 활용한 고속 프론트엔드 구현**
    - Claude를 활용한 Vibe Coding 기법으로, 복잡한 Flutter UI와 상태 관리 로직 구축

      <br />
- **UE Remote Control Plugin HTTP API를 통한 런타임 액터 제어**
    - Remote Control Plugin(포트 30010)의 HTTP API를 통해 런타임 중인 언리얼 엔진 내 NPC 액터의 행동(이동, 점프, 공격)을 외부에서 직접 제어
<br />

***

### ✅ 구조도

<br />

<img width="621" height="201" alt="Image" src="https://github.com/user-attachments/assets/804bb606-2f68-41b3-9446-4f8c53b4183d" />

<br />

***


### ✅ 구현 영상

<br />

![Image](https://github.com/user-attachments/assets/1a8a8dab-5875-44ef-9b40-ab81a45789dd)
