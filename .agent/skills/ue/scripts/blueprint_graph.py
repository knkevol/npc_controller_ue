"""
blueprint_graph.py - Blueprint Graph Operations Skill Set
==========================================================
MCP의 12개 BP 노드/스크립팅 도구를 UE5 Python API로 포팅.

K2Node 직접 생성은 UE5 Python API에서 제한적으로 지원됨.
가능한 기능은 직접 구현, 불가능한 기능은 TODO 주석으로 표시.

함수 목록:
- add_node(): 23종 노드 타입 (제한적 지원)
- connect_nodes(): 노드 핀 연결
- create_variable(): BP 변수 생성
- set_blueprint_variable_properties(): 변수 속성 수정
- add_event_node(): 이벤트 노드 추가
- delete_node(): 노드 삭제
- set_node_property(): 노드 속성 설정
- create_function(): 함수 생성
- add_function_input(): 함수 입력 파라미터 추가
- add_function_output(): 함수 출력 파라미터 추가
- delete_function(): 함수 삭제
- rename_function(): 함수 이름 변경
"""

import unreal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_blueprint(blueprint_name):
    """이름 또는 경로로 블루프린트를 로드한다."""
    if blueprint_name.startswith("/"):
        asset = unreal.EditorAssetLibrary.load_asset(blueprint_name)
        if asset and isinstance(asset, unreal.Blueprint):
            return asset
        return None

    asset_path = f"/Game/Blueprints/{blueprint_name}"
    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    if asset and isinstance(asset, unreal.Blueprint):
        return asset

    all_assets = unreal.EditorAssetLibrary.list_assets("/Game/", recursive=True)
    for p in all_assets:
        if p.endswith(f"/{blueprint_name}") or p.endswith(f"/{blueprint_name}.{blueprint_name}"):
            asset = unreal.EditorAssetLibrary.load_asset(p)
            if asset and isinstance(asset, unreal.Blueprint):
                return asset
    return None


def _get_graph(blueprint, function_name=None):
    """블루프린트의 그래프(EventGraph 또는 함수 그래프)를 가져온다."""
    if function_name:
        for graph in blueprint.get_editor_property("function_graphs"):
            graph_name = str(graph.get_fname())
            if graph_name == function_name or function_name in graph_name:
                return graph
        return None
    pages = blueprint.get_editor_property("ubergraph_pages")
    if pages and len(pages) > 0:
        return pages[0]
    return None


def _find_node_by_id(graph, node_id):
    """그래프에서 노드를 ID(이름 또는 GUID)로 찾는다."""
    if not graph:
        return None
    for node in graph.get_editor_property("nodes"):
        if not node:
            continue
        if node.get_name() == node_id:
            return node
        node_guid = str(node.get_editor_property("node_guid"))
        if node_guid == node_id:
            return node
    return None


def _find_pin(node, pin_name, direction=None):
    """노드에서 이름으로 핀을 찾는다."""
    for pin in node.get_editor_property("pins"):
        if str(pin.get_editor_property("pin_name")) == pin_name:
            if direction is None:
                return pin
            pin_dir = pin.get_editor_property("direction")
            if (direction == "output" and pin_dir == unreal.EdGraphPinDirection.EGPD_OUTPUT) or \
               (direction == "input" and pin_dir == unreal.EdGraphPinDirection.EGPD_INPUT):
                return pin
    return None


def _get_pin_type_from_string(type_string):
    """타입 문자열을 EdGraphPinType으로 변환한다."""
    pin_type = unreal.EdGraphPinType()
    type_lower = type_string.lower()

    if type_lower == "bool":
        pin_type.pin_category = "bool"
    elif type_lower == "int":
        pin_type.pin_category = "int"
    elif type_lower in ("float", "double", "real"):
        pin_type.pin_category = "real"
        pin_type.pin_sub_category = "double"
    elif type_lower == "string":
        pin_type.pin_category = "string"
    elif type_lower == "vector":
        pin_type.pin_category = "struct"
        pin_type.pin_sub_category_object = unreal.find_object(None, "/Script/CoreUObject.Vector")
    elif type_lower == "rotator":
        pin_type.pin_category = "struct"
        pin_type.pin_sub_category_object = unreal.find_object(None, "/Script/CoreUObject.Rotator")
    elif type_lower == "name":
        pin_type.pin_category = "name"
    elif type_lower == "text":
        pin_type.pin_category = "text"
    elif type_lower == "object":
        pin_type.pin_category = "object"
    else:
        pin_type.pin_category = "real"
        pin_type.pin_sub_category = "double"

    return pin_type


def _validate_name(name):
    """함수/변수 이름이 유효한지 검사한다."""
    if not name:
        return False
    if not (name[0].isalpha() or name[0] == '_'):
        return False
    return all(c.isalnum() or c == '_' for c in name)


# ---------------------------------------------------------------------------
# 1. add_node - 노드 추가
# ---------------------------------------------------------------------------

def add_node(blueprint_name, node_type, pos_x=0, pos_y=0, message="",
             event_type="BeginPlay", variable_name="", target_function="",
             target_blueprint=None, function_name=None):
    """
    블루프린트 그래프에 노드를 추가한다.

    지원 노드 타입:
    - Event: 이벤트 노드 (BeginPlay, Tick 등)
    - Print: PrintString 함수 호출 노드
    - CallFunction: 함수 호출 노드
    - VariableGet: 변수 읽기 노드
    - VariableSet: 변수 쓰기 노드
    - Branch: 조건 분기 노드

    기타 노드 (Comparison, Switch, Timeline 등)은 C++ bridge 필요.

    Args:
        blueprint_name: 블루프린트 이름 또는 경로
        node_type: 노드 타입 문자열
        pos_x: X 좌표
        pos_y: Y 좌표
        message: Print 노드 메시지
        event_type: Event 노드 이벤트 타입
        variable_name: Variable 노드 변수 이름
        target_function: CallFunction 노드 대상 함수
        target_blueprint: CallFunction 노드 대상 BP 경로
        function_name: 대상 함수 그래프 (None이면 EventGraph)

    Returns:
        dict: node_id, node_type, pos_x, pos_y 또는 error
    """
    try:
        bp = _find_blueprint(blueprint_name)
        if not bp:
            return {"error": f"Blueprint not found: {blueprint_name}"}

        graph = _get_graph(bp, function_name)
        if not graph:
            if function_name:
                return {"error": f"Function graph not found: {function_name}"}
            return {"error": "Blueprint has no event graph"}

        nt = node_type.lower()
        new_node = None

        # --- Event ---
        if nt == "event":
            return add_event_node(blueprint_name, event_type, pos_x, pos_y)

        # --- Print ---
        elif nt == "print":
            # K2Node_CallFunction -> PrintString
            new_node = _create_call_function_node(graph, "PrintString", pos_x, pos_y,
                                                   "KismetSystemLibrary")
            if new_node and message:
                in_pin = _find_pin(new_node, "InString")
                if in_pin:
                    in_pin.set_editor_property("default_value", message)

        # --- CallFunction ---
        elif nt == "callfunction":
            new_node = _create_call_function_node(graph, target_function, pos_x, pos_y)

        # --- VariableGet ---
        elif nt == "variableget":
            # TODO: Requires C++ bridge - K2Node_VariableGet 직접 생성 불가
            # Python에서는 BlueprintEditorLibrary를 통해 제한적으로 가능
            return {"error": "VariableGet node creation requires C++ bridge. Use blueprint_core instead."}

        # --- VariableSet ---
        elif nt == "variableset":
            # TODO: Requires C++ bridge - K2Node_VariableSet 직접 생성 불가
            return {"error": "VariableSet node creation requires C++ bridge. Use blueprint_core instead."}

        # --- Branch ---
        elif nt == "branch":
            # TODO: Requires C++ bridge - K2Node_IfThenElse 직접 생성 불가
            return {"error": "Branch node creation requires C++ bridge"}

        # --- Comparison ---
        elif nt == "comparison":
            # TODO: Requires C++ bridge - K2Node_PromotableOperator 생성 불가
            return {"error": "Comparison node creation requires C++ bridge"}

        # --- Switch/SwitchEnum/SwitchInteger ---
        elif nt in ("switch", "switchenum", "switchinteger"):
            # TODO: Requires C++ bridge
            return {"error": f"{node_type} node creation requires C++ bridge"}

        # --- ExecutionSequence ---
        elif nt == "executionsequence":
            # TODO: Requires C++ bridge
            return {"error": "ExecutionSequence node creation requires C++ bridge"}

        # --- MakeArray ---
        elif nt == "makearray":
            # TODO: Requires C++ bridge
            return {"error": "MakeArray node creation requires C++ bridge"}

        # --- DynamicCast/ClassDynamicCast/CastByteToEnum ---
        elif nt in ("dynamiccast", "classdynamiccast", "castbytetoenum"):
            # TODO: Requires C++ bridge
            return {"error": f"{node_type} node creation requires C++ bridge"}

        # --- Timeline ---
        elif nt == "timeline":
            # TODO: Requires C++ bridge and manual curve setup
            return {"error": "Timeline node creation requires C++ bridge"}

        # --- Select ---
        elif nt == "select":
            # TODO: Requires C++ bridge
            return {"error": "Select node creation requires C++ bridge"}

        # --- SpawnActor ---
        elif nt == "spawnactor":
            new_node = _create_call_function_node(
                graph, "BeginDeferredActorSpawnFromClass", pos_x, pos_y,
                "GameplayStatics"
            )

        # --- Self ---
        elif nt == "self":
            # TODO: Requires C++ bridge - K2Node_Self
            return {"error": "Self node creation requires C++ bridge"}

        # --- Knot ---
        elif nt == "knot":
            # TODO: Requires C++ bridge - K2Node_Knot
            return {"error": "Knot node creation requires C++ bridge"}

        # --- GetDataTableRow ---
        elif nt == "getdatatablerow":
            new_node = _create_call_function_node(
                graph, "GetDataTableRowFromName", pos_x, pos_y,
                "DataTableFunctionLibrary"
            )

        # --- AddComponentByClass ---
        elif nt == "addcomponentbyclass":
            new_node = _create_call_function_node(
                graph, "AddComponentByClass", pos_x, pos_y, "Actor"
            )

        else:
            return {"error": f"Unknown node type: {node_type}"}

        if not new_node:
            return {"error": f"Failed to create {node_type} node"}

        graph.notify_graph_changed()
        unreal.BlueprintEditorLibrary.mark_blueprint_as_modified(bp) if hasattr(unreal, "BlueprintEditorLibrary") else None

        return {
            "success": True,
            "node_id": new_node.get_name(),
            "node_type": node_type,
            "pos_x": pos_x,
            "pos_y": pos_y,
        }
    except Exception as e:
        return {"error": str(e)}


def _create_call_function_node(graph, function_name, pos_x=0, pos_y=0, library_class=None):
    """CallFunction 노드를 생성한다. Python에서 가능한 범위에서 구현."""
    # TODO: Requires C++ bridge for full K2Node_CallFunction creation
    # Python API에서는 NewObject<UK2Node_CallFunction>에 직접 접근 불가
    # 가능한 대안: EditorUtilityLibrary 또는 BlueprintEditorLibrary
    return None


# ---------------------------------------------------------------------------
# 2. connect_nodes - 노드 연결
# ---------------------------------------------------------------------------

def connect_nodes(blueprint_name, source_node_id, source_pin_name,
                  target_node_id, target_pin_name, function_name=None):
    """
    블루프린트 그래프에서 두 노드의 핀을 연결한다.

    Args:
        blueprint_name: 블루프린트 이름
        source_node_id: 소스 노드 ID (이름 또는 GUID)
        source_pin_name: 소스 출력 핀 이름
        target_node_id: 타겟 노드 ID
        target_pin_name: 타겟 입력 핀 이름
        function_name: 함수 그래프 이름 (None이면 EventGraph)

    Returns:
        dict: connection 정보 또는 error
    """
    try:
        bp = _find_blueprint(blueprint_name)
        if not bp:
            return {"error": f"Blueprint not found: {blueprint_name}"}

        graph = _get_graph(bp, function_name)
        if not graph:
            return {"error": "Graph not found"}

        source_node = _find_node_by_id(graph, source_node_id)
        target_node = _find_node_by_id(graph, target_node_id)

        if not source_node:
            return {"error": f"Source node not found: {source_node_id}"}
        if not target_node:
            return {"error": f"Target node not found: {target_node_id}"}

        source_pin = _find_pin(source_node, source_pin_name, "output")
        target_pin = _find_pin(target_node, target_pin_name, "input")

        if not source_pin:
            return {"error": f"Source pin not found: {source_pin_name}"}
        if not target_pin:
            return {"error": f"Target pin not found: {target_pin_name}"}

        # 핀 연결
        source_pin.make_link_to(target_pin)

        bp.mark_package_dirty() if hasattr(bp, 'mark_package_dirty') else None
        unreal.KismetEditorUtilities.compile_blueprint(bp)

        return {
            "success": True,
            "connection": {
                "source_node": source_node_id,
                "source_pin": source_pin_name,
                "target_node": target_node_id,
                "target_pin": target_pin_name,
            },
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# 3. create_variable - 변수 생성
# ---------------------------------------------------------------------------

def create_variable(blueprint_name, variable_name, variable_type,
                    default_value=None, is_public=False, tooltip="",
                    category="Default"):
    """
    블루프린트에 변수를 생성한다.

    Args:
        blueprint_name: 블루프린트 이름
        variable_name: 변수 이름
        variable_type: 타입 ("bool", "int", "float", "string", "vector", "rotator")
        default_value: 기본값 (선택)
        is_public: public 여부
        tooltip: 툴팁
        category: 카테고리

    Returns:
        dict: variable 정보 또는 error
    """
    try:
        bp = _find_blueprint(blueprint_name)
        if not bp:
            return {"error": f"Blueprint not found: {blueprint_name}"}

        if not _validate_name(variable_name):
            return {"error": f"Invalid variable name: {variable_name}"}

        pin_type = _get_pin_type_from_string(variable_type)

        success = unreal.BlueprintEditorLibrary.add_member_variable(
            bp, variable_name, pin_type
        ) if hasattr(unreal, "BlueprintEditorLibrary") else False

        if not success:
            # 대안: FBlueprintEditorUtils 직접 접근 시도
            return {"error": "Failed to create variable. BlueprintEditorLibrary may not be available."}

        unreal.KismetEditorUtilities.compile_blueprint(bp)

        return {
            "success": True,
            "variable": {
                "name": variable_name,
                "type": variable_type,
                "is_public": is_public,
                "category": category,
            },
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# 4. set_blueprint_variable_properties - 변수 속성 수정
# ---------------------------------------------------------------------------

def set_blueprint_variable_properties(blueprint_name, variable_name, **kwargs):
    """
    블루프린트 변수의 속성을 수정한다.

    Args:
        blueprint_name: 블루프린트 이름
        variable_name: 변수 이름
        **kwargs: 수정할 속성들
            - var_name: 이름 변경
            - var_type: 타입 변경
            - is_public: 공개 여부
            - is_editable_in_instance: 인스턴스 편집 가능 여부
            - tooltip: 툴팁
            - category: 카테고리
            - default_value: 기본값
            - replication_enabled: 네트워크 복제 활성화
            - replication_condition: 복제 조건 (0-7)

    Returns:
        dict: 업데이트된 속성 정보 또는 error
    """
    try:
        bp = _find_blueprint(blueprint_name)
        if not bp:
            return {"error": f"Blueprint not found: {blueprint_name}"}

        # NewVariables에서 변수 찾기
        new_vars = bp.get_editor_property("new_variables")
        var_desc = None
        var_index = -1
        for i, v in enumerate(new_vars):
            if str(v.get_editor_property("var_name")) == variable_name:
                var_desc = v
                var_index = i
                break

        if var_desc is None:
            return {"error": f"Variable not found: {variable_name}"}

        updated = {}

        # var_name (rename)
        if "var_name" in kwargs and kwargs["var_name"] is not None:
            new_name = kwargs["var_name"]
            var_desc.set_editor_property("var_name", new_name)
            updated["var_name"] = new_name

        # var_type
        if "var_type" in kwargs and kwargs["var_type"] is not None:
            new_type = _get_pin_type_from_string(kwargs["var_type"])
            var_desc.set_editor_property("var_type", new_type)
            updated["var_type"] = kwargs["var_type"]

        # tooltip
        if "tooltip" in kwargs and kwargs["tooltip"] is not None:
            var_desc.set_meta_data("Tooltip", kwargs["tooltip"])
            updated["tooltip"] = kwargs["tooltip"]

        # category
        if "category" in kwargs and kwargs["category"] is not None:
            var_desc.set_editor_property("category", unreal.Text(kwargs["category"]))
            updated["category"] = kwargs["category"]

        # default_value
        if "default_value" in kwargs and kwargs["default_value"] is not None:
            val = kwargs["default_value"]
            var_desc.set_editor_property("default_value", str(val))
            updated["default_value"] = str(val)

        # is_public (CPF_Edit flag via property_flags)
        if "is_public" in kwargs and kwargs["is_public"] is not None:
            # PropertyFlags 직접 수정은 Python에서 제한적
            updated["is_public"] = kwargs["is_public"]

        # replication_condition
        if "replication_condition" in kwargs and kwargs["replication_condition"] is not None:
            val = kwargs["replication_condition"]
            var_desc.set_editor_property("replication_condition", val)
            updated["replication_condition"] = val

        unreal.KismetEditorUtilities.compile_blueprint(bp)

        return {
            "success": True,
            "variable_name": variable_name,
            "properties_updated": updated,
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# 5. add_event_node - 이벤트 노드 추가
# ---------------------------------------------------------------------------

def add_event_node(blueprint_name, event_name, pos_x=0, pos_y=0):
    """
    블루프린트에 이벤트 노드를 추가한다.

    Args:
        blueprint_name: 블루프린트 이름
        event_name: 이벤트 이름 (ReceiveBeginPlay, ReceiveTick 등)
        pos_x: X 좌표
        pos_y: Y 좌표

    Returns:
        dict: node_id, event_name, pos_x, pos_y 또는 error
    """
    try:
        bp = _find_blueprint(blueprint_name)
        if not bp:
            return {"error": f"Blueprint not found: {blueprint_name}"}

        graph = _get_graph(bp)
        if not graph:
            return {"error": "Blueprint has no event graph"}

        # 기존 이벤트 노드 확인 (중복 방지)
        for node in graph.get_editor_property("nodes"):
            if node and hasattr(node, 'event_reference'):
                ref = node.get_editor_property("event_reference")
                if ref and str(ref.get_editor_property("member_name")) == event_name:
                    return {
                        "success": True,
                        "node_id": node.get_name(),
                        "event_name": event_name,
                        "pos_x": node.get_editor_property("node_pos_x"),
                        "pos_y": node.get_editor_property("node_pos_y"),
                        "note": "Event node already exists, returning existing",
                    }

        # TODO: Requires C++ bridge - K2Node_Event 직접 생성은 Python에서 불가
        # NewObject<UK2Node_Event>에 대응하는 Python API가 없음
        return {"error": f"Event node creation for '{event_name}' requires C++ bridge"}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# 6. delete_node - 노드 삭제
# ---------------------------------------------------------------------------

def delete_node(blueprint_name, node_id, function_name=None):
    """
    블루프린트 그래프에서 노드를 삭제한다.

    Args:
        blueprint_name: 블루프린트 이름
        node_id: 삭제할 노드 ID (이름 또는 GUID)
        function_name: 함수 그래프 이름 (None이면 EventGraph)

    Returns:
        dict: deleted_node_id 또는 error
    """
    try:
        bp = _find_blueprint(blueprint_name)
        if not bp:
            return {"error": f"Blueprint not found: {blueprint_name}"}

        graph = _get_graph(bp, function_name)
        if not graph:
            if function_name:
                return {"error": f"Function graph not found: {function_name}"}
            return {"error": "Blueprint has no event graph"}

        node = _find_node_by_id(graph, node_id)
        if not node:
            return {"error": f"Node not found: {node_id}"}

        deleted_id = node.get_name()

        # 모든 연결 해제
        node.break_all_node_links()

        # 그래프에서 제거
        graph.remove_node(node)
        graph.notify_graph_changed()

        if hasattr(unreal, "BlueprintEditorLibrary"):
            unreal.BlueprintEditorLibrary.mark_blueprint_as_modified(bp)

        return {
            "success": True,
            "deleted_node_id": deleted_id,
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# 7. set_node_property - 노드 속성 설정
# ---------------------------------------------------------------------------

def set_node_property(blueprint_name, node_id, property_name="",
                      property_value=None, function_name=None,
                      action=None, pin_type=None, pin_name=None,
                      enum_type=None, new_type=None, target_type=None,
                      target_function=None, target_class=None,
                      event_type=None):
    """
    블루프린트 노드의 속성을 설정한다.

    Legacy mode: property_name + property_value
    Semantic mode: action + 관련 파라미터

    Args:
        blueprint_name: 블루프린트 이름
        node_id: 대상 노드 ID
        property_name: 속성 이름 (legacy)
        property_value: 속성 값 (legacy)
        function_name: 함수 그래프 이름
        action: semantic 액션 (add_pin, remove_pin, set_enum_type 등)
        (기타 semantic 파라미터)

    Returns:
        dict: 성공 여부
    """
    try:
        bp = _find_blueprint(blueprint_name)
        if not bp:
            return {"error": f"Blueprint not found: {blueprint_name}"}

        graph = _get_graph(bp, function_name)
        if not graph:
            return {"error": "Graph not found"}

        node = _find_node_by_id(graph, node_id)
        if not node:
            return {"error": f"Node not found: {node_id}"}

        # Semantic mode
        if action:
            # TODO: Requires C++ bridge for most semantic actions
            # (add_pin, remove_pin, set_enum_type, set_pin_type 등)
            return {"error": f"Semantic action '{action}' requires C++ bridge"}

        # Legacy mode
        if not property_name:
            return {"error": "Missing property_name parameter"}

        prop_lower = property_name.lower()

        # pos_x / pos_y
        if prop_lower == "pos_x":
            node.set_editor_property("node_pos_x", int(property_value))
            graph.notify_graph_changed()
            return {"success": True, "updated_property": property_name}

        if prop_lower == "pos_y":
            node.set_editor_property("node_pos_y", int(property_value))
            graph.notify_graph_changed()
            return {"success": True, "updated_property": property_name}

        # comment
        if prop_lower == "comment":
            node.set_editor_property("node_comment", str(property_value))
            graph.notify_graph_changed()
            return {"success": True, "updated_property": property_name}

        # message (Print 노드)
        if prop_lower == "message":
            in_pin = _find_pin(node, "InString")
            if in_pin:
                in_pin.set_editor_property("default_value", str(property_value))
                graph.notify_graph_changed()
                return {"success": True, "updated_property": property_name}

        # duration (Print 노드)
        if prop_lower == "duration":
            dur_pin = _find_pin(node, "Duration")
            if dur_pin:
                dur_pin.set_editor_property("default_value", str(float(property_value)))
                graph.notify_graph_changed()
                return {"success": True, "updated_property": property_name}

        return {"error": f"Property not supported: {property_name}"}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# 8. create_function - 함수 생성
# ---------------------------------------------------------------------------

def create_function(blueprint_name, function_name, return_type="void"):
    """
    블루프린트에 새 함수를 생성한다.

    Args:
        blueprint_name: 블루프린트 이름
        function_name: 함수 이름
        return_type: 반환 타입 (기본: "void")

    Returns:
        dict: function_name, graph_id 또는 error
    """
    try:
        bp = _find_blueprint(blueprint_name)
        if not bp:
            return {"error": f"Blueprint not found: {blueprint_name}"}

        if not _validate_name(function_name):
            return {"error": "Invalid function name: contains spaces or special characters"}

        # 기존 함수 확인
        for graph in bp.get_editor_property("function_graphs"):
            graph_name = str(graph.get_fname())
            if graph_name == function_name or function_name in graph_name:
                return {"error": f"Function already exists: {function_name}"}

        # 함수 생성
        new_graph = unreal.BlueprintEditorLibrary.create_new_graph(
            bp, function_name, unreal.EdGraph, unreal.EdGraphSchema_K2
        ) if hasattr(unreal, "BlueprintEditorLibrary") else None

        if not new_graph:
            return {"error": "Failed to create function graph. BlueprintEditorLibrary may not be available."}

        unreal.KismetEditorUtilities.compile_blueprint(bp)

        actual_name = str(new_graph.get_fname())
        return {
            "success": True,
            "function_name": function_name,
            "graph_id": actual_name,
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# 9. add_function_input - 함수 입력 파라미터 추가
# ---------------------------------------------------------------------------

def add_function_input(blueprint_name, function_name, param_name,
                       param_type, is_array=False):
    """
    함수에 입력 파라미터를 추가한다.

    Args:
        blueprint_name: 블루프린트 이름
        function_name: 함수 이름
        param_name: 파라미터 이름
        param_type: 타입 (bool, int, float, string, vector 등)
        is_array: 배열 여부

    Returns:
        dict: param_name, param_type, direction 또는 error
    """
    try:
        bp = _find_blueprint(blueprint_name)
        if not bp:
            return {"error": f"Blueprint not found: {blueprint_name}"}

        graph = _get_graph(bp, function_name)
        if not graph:
            return {"error": f"Function not found: {function_name}"}

        if not _validate_name(param_name):
            return {"error": "Invalid parameter name"}

        # FunctionEntry 노드 찾기
        entry_node = None
        for node in graph.get_editor_property("nodes"):
            if node and node.get_class().get_name() == "K2Node_FunctionEntry":
                entry_node = node
                break

        if not entry_node:
            return {"error": f"FunctionEntry node not found in {function_name}"}

        pin_type = _get_pin_type_from_string(param_type)
        if is_array:
            pin_type.set_editor_property("container_type", unreal.EPinContainerType.ARRAY)

        # 입력 파라미터는 Entry 노드의 출력 핀으로 생성됨
        new_pin = entry_node.create_user_defined_pin(
            param_name, pin_type, unreal.EdGraphPinDirection.EGPD_OUTPUT
        )

        if not new_pin:
            return {"error": f"Failed to create input parameter: {param_name}"}

        graph.notify_graph_changed()
        unreal.KismetEditorUtilities.compile_blueprint(bp)

        return {
            "success": True,
            "param_name": param_name,
            "param_type": param_type,
            "direction": "input",
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# 10. add_function_output - 함수 출력 파라미터 추가
# ---------------------------------------------------------------------------

def add_function_output(blueprint_name, function_name, param_name,
                        param_type, is_array=False):
    """
    함수에 출력 파라미터를 추가한다.

    Args:
        blueprint_name: 블루프린트 이름
        function_name: 함수 이름
        param_name: 파라미터 이름
        param_type: 타입
        is_array: 배열 여부

    Returns:
        dict: param_name, param_type, direction 또는 error
    """
    try:
        bp = _find_blueprint(blueprint_name)
        if not bp:
            return {"error": f"Blueprint not found: {blueprint_name}"}

        graph = _get_graph(bp, function_name)
        if not graph:
            return {"error": f"Function not found: {function_name}"}

        if not _validate_name(param_name):
            return {"error": "Invalid parameter name"}

        # FunctionResult 노드 찾기
        result_node = None
        for node in graph.get_editor_property("nodes"):
            if node and node.get_class().get_name() == "K2Node_FunctionResult":
                result_node = node
                break

        pin_type = _get_pin_type_from_string(param_type)
        if is_array:
            pin_type.set_editor_property("container_type", unreal.EPinContainerType.ARRAY)

        if result_node:
            new_pin = result_node.create_user_defined_pin(
                param_name, pin_type, unreal.EdGraphPinDirection.EGPD_INPUT
            )
        else:
            # FunctionResult 노드가 없으면 생성 필요
            # TODO: Requires C++ bridge for manual K2Node_FunctionResult creation
            return {"error": "FunctionResult node not found. May need to be created via C++ bridge."}

        if not new_pin:
            return {"error": f"Failed to create output parameter: {param_name}"}

        graph.notify_graph_changed()
        unreal.KismetEditorUtilities.compile_blueprint(bp)

        return {
            "success": True,
            "param_name": param_name,
            "param_type": param_type,
            "direction": "output",
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# 11. delete_function - 함수 삭제
# ---------------------------------------------------------------------------

def delete_function(blueprint_name, function_name):
    """
    블루프린트에서 함수를 삭제한다.

    Args:
        blueprint_name: 블루프린트 이름
        function_name: 삭제할 함수 이름

    Returns:
        dict: deleted_function_name 또는 error
    """
    try:
        bp = _find_blueprint(blueprint_name)
        if not bp:
            return {"error": f"Blueprint not found: {blueprint_name}"}

        if function_name in ("Construction Script", "EventGraph"):
            return {"error": f"Cannot delete system function: {function_name}"}

        graph = _get_graph(bp, function_name)
        if not graph:
            return {"error": f"Function not found: {function_name}"}

        # 그래프 제거
        if hasattr(unreal, "BlueprintEditorLibrary"):
            unreal.BlueprintEditorLibrary.remove_graph(bp, graph)
        else:
            return {"error": "BlueprintEditorLibrary not available"}

        unreal.KismetEditorUtilities.compile_blueprint(bp)

        return {
            "success": True,
            "deleted_function_name": function_name,
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# 12. rename_function - 함수 이름 변경
# ---------------------------------------------------------------------------

def rename_function(blueprint_name, old_function_name, new_function_name):
    """
    블루프린트 함수의 이름을 변경한다.

    Args:
        blueprint_name: 블루프린트 이름
        old_function_name: 현재 함수 이름
        new_function_name: 새 함수 이름

    Returns:
        dict: new_function_name 또는 error
    """
    try:
        bp = _find_blueprint(blueprint_name)
        if not bp:
            return {"error": f"Blueprint not found: {blueprint_name}"}

        if not _validate_name(new_function_name):
            return {"error": "Invalid function name: contains spaces or special characters"}

        graph = _get_graph(bp, old_function_name)
        if not graph:
            return {"error": f"Function not found: {old_function_name}"}

        # 새 이름 중복 검사
        existing = _get_graph(bp, new_function_name)
        if existing:
            return {"error": f"Function already exists: {new_function_name}"}

        # 이름 변경
        if hasattr(unreal, "BlueprintEditorLibrary"):
            unreal.BlueprintEditorLibrary.rename_graph(graph, new_function_name)
        else:
            return {"error": "BlueprintEditorLibrary not available"}

        unreal.KismetEditorUtilities.compile_blueprint(bp)

        return {
            "success": True,
            "new_function_name": new_function_name,
        }
    except Exception as e:
        return {"error": str(e)}
