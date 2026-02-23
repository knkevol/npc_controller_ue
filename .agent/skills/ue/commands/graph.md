---
description: UE5 Blueprint 그래프 노드 추가/연결/삭제/속성 설정
allowed-tools: Bash(curl:*)
argument-hint: <action> <bp_name> [options...] (예: add-node MyBP Branch, connect MyBP node1 exec node2 exec)
---

Blueprint 그래프 노드를 조작해라.

## 사용 가능한 함수 (skills.blueprint_graph)

- `add_node(blueprint_name, node_type, pos_x=0, pos_y=0, message="", event_type="BeginPlay", variable_name="", target_function="", target_blueprint=None, function_name=None)`
  - node_type: Event, Branch, Comparison, Switch, Print, CallFunction, VariableGet, VariableSet, DynamicCast, Select, SpawnActor, Timeline, Self, Knot, ExecutionSequence, MakeArray, SwitchEnum, SwitchInteger, ClassDynamicCast, CastByteToEnum, GetDataTableRow, AddComponentByClass
- `connect_nodes(blueprint_name, source_node_id, source_pin_name, target_node_id, target_pin_name, function_name=None)`
- `add_event_node(blueprint_name, event_name, pos_x=0, pos_y=0)`
- `delete_node(blueprint_name, node_id, function_name=None)`
- `set_node_property(blueprint_name, node_id, property_name="", property_value=None, action=None, ...)`

사용자 요청: $ARGUMENTS
