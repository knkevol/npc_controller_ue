---
description: UE5 Blueprint 생성/수정/컴파일/읽기
allowed-tools: Bash(curl:*)
argument-hint: <action> <bp_name> [options...] (예: create MyBP Actor, read /Game/BP_Test, compile MyBP)
---

Blueprint 작업을 수행해라.

## 사용 가능한 함수

**생성/수정 (skills.blueprint_core)**:
- `create_blueprint(name, parent_class, path="/Game/Blueprints")`
- `add_component_to_blueprint(blueprint_name, component_type, component_name, location=[], rotation=[], scale=[], component_properties={})`
- `set_static_mesh_properties(blueprint_name, component_name, static_mesh)`
- `set_physics_properties(blueprint_name, component_name, simulate_physics, gravity_enabled, mass, linear_damping, angular_damping)`
- `compile_blueprint(blueprint_name)`

**읽기 (skills.blueprint_read)**:
- `read_blueprint_content(blueprint_path, include_event_graph=True, include_functions=True, include_variables=True, include_components=True, include_interfaces=True)`
- `analyze_blueprint_graph(blueprint_path, graph_name="EventGraph")`
- `get_blueprint_variable_details(blueprint_path, variable_name=None)`
- `get_blueprint_function_details(blueprint_path, function_name=None, include_graph=True)`

## 호출 방법

```bash
curl -s -X POST http://127.0.0.1:8080/execute -H "Content-Type: application/json" -d "{\"mode\":\"editor\",\"script\":\"from skills.blueprint_core import create_blueprint\\nresult.update(create_blueprint(params['name'], params['parent_class']))\",\"params\":{\"name\":\"BP_Test\",\"parent_class\":\"Actor\"}}"
```

사용자 요청: $ARGUMENTS
