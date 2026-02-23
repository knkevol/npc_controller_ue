---
description: UE5 머티리얼 검색/적용/색상 설정
allowed-tools: Bash(curl:*)
argument-hint: <action> [args...] (예: list, apply MyActor /Game/Mat, color MyBP MeshComp 1,0,0)
---

머티리얼 작업을 수행해라.

## 사용 가능한 함수 (skills.material_ops)

- `get_available_materials(search_path="/Game/", include_engine_materials=True)`
- `apply_material_to_actor(actor_name, material_path, material_slot=0)`
- `apply_material_to_blueprint(blueprint_name, component_name, material_path, material_slot=0)`
- `get_actor_material_info(actor_name)`
- `set_mesh_material_color(blueprint_name, component_name, color, material_path=None, parameter_name="BaseColor", material_slot=0)`
  - color: [R, G, B] 또는 [R, G, B, A] (0.0~1.0)

사용자 요청: $ARGUMENTS
