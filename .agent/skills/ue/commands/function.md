---
description: UE5 Blueprint 함수 생성/삭제/이름변경/파라미터 추가
allowed-tools: Bash(curl:*)
argument-hint: <action> <bp_name> <func_name> [options...] (예: create MyBP DoAttack, add-input MyBP DoAttack Damage float)
---

Blueprint 함수를 관리해라.

## 사용 가능한 함수 (skills.blueprint_graph)

- `create_function(blueprint_name, function_name, return_type="void")`
- `add_function_input(blueprint_name, function_name, param_name, param_type, is_array=False)`
- `add_function_output(blueprint_name, function_name, param_name, param_type, is_array=False)`
- `delete_function(blueprint_name, function_name)`
- `rename_function(blueprint_name, old_function_name, new_function_name)`

사용자 요청: $ARGUMENTS
