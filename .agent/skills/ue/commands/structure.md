---
description: UE5 구조물 생성 (피라미드, 벽, 타워, 계단, 아치, 집, 맨션, 다리, 수도교, 미로, 마을, 성채)
allowed-tools: Bash(curl:*)
argument-hint: <구조물 타입> [옵션...] (예: pyramid base_size=5, house modern, castle large)
---

UE5에 구조물을 생성해라.

## 구조물별 함수

| 구조물 | 모듈 | 함수 | 주요 파라미터 |
|--------|------|------|-------------|
| pyramid | structures.primitives | create_pyramid | base_size, block_size, location |
| wall | structures.primitives | create_wall | length, height, block_size, orientation(x/y) |
| tower | structures.buildings | create_tower | height, base_size, tower_style(cylindrical/square/tapered) |
| staircase | structures.primitives | create_staircase | steps, step_size |
| arch | structures.primitives | create_arch | radius, segments |
| house | structures.buildings | construct_house | width, depth, height, house_style(modern/cottage) |
| mansion | structures.buildings | construct_mansion | mansion_scale(small/large/epic/legendary) |
| bridge | structures.engineering | create_suspension_bridge | span_length, deck_width, tower_height |
| aqueduct | structures.engineering | create_aqueduct | arches, arch_radius, tiers |
| maze | structures.complex | create_maze | rows, cols, cell_size, wall_height |
| town | structures.complex | create_town | town_size(small/medium/large), architectural_style |
| castle | structures.complex | create_castle_fortress | castle_size, include_village, include_siege_weapons |

## 호출 예시

```bash
curl -s -X POST http://127.0.0.1:8080/execute -H "Content-Type: application/json" -d "{\"mode\":\"editor\",\"script\":\"from skills.structures.primitives import create_pyramid\\nresult.update(create_pyramid(base_size=5, location=[0,0,0]))\",\"params\":{}}"
```

사용자 요청: $ARGUMENTS
