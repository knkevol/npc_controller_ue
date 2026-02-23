---
description: UE5 Blueprint 변수 생성/속성 수정
allowed-tools: Bash(curl:*)
argument-hint: <action> <bp_name> <var_name> [type] [options...] (예: create MyBP Health float, set MyBP Health is_public=true)
---

Blueprint 변수를 관리해라.

## 사용 가능한 함수 (skills.blueprint_graph)

- `create_variable(blueprint_name, variable_name, variable_type, default_value=None, is_public=False, tooltip="", category="Default")`
  - variable_type: bool, int, float, string, vector, rotator
- `set_blueprint_variable_properties(blueprint_name, variable_name, var_name=None, var_type=None, is_public=None, is_editable_in_instance=None, tooltip=None, category=None, default_value=None, ...)`

사용자 요청: $ARGUMENTS
