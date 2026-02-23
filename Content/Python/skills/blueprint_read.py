"""
Blueprint Read Operations
=========================
BP 내부 구조를 읽는 4개 함수.
변수, 함수, 이벤트 그래프, 컴포넌트, 인터페이스 정보를 dict로 반환.
"""
import unreal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_blueprint(blueprint_path):
    """경로로 Blueprint를 로드한다."""
    asset = unreal.EditorAssetLibrary.load_asset(blueprint_path)
    if asset and isinstance(asset, unreal.Blueprint):
        return asset
    return None


def _node_to_dict(node, include_details=False, include_pins=False):
    """EdGraphNode를 dict로 변환."""
    info = {
        "name": node.get_name(),
        "class": node.get_class().get_name(),
        "title": node.get_node_title(unreal.NodeTitleType.FULL_TITLE) if hasattr(unreal, "NodeTitleType") else node.get_name(),
    }
    if include_details:
        info["pos_x"] = node.node_pos_x if hasattr(node, "node_pos_x") else 0
        info["pos_y"] = node.node_pos_y if hasattr(node, "node_pos_y") else 0
    if include_pins:
        pins = []
        for pin in node.pins if hasattr(node, "pins") else []:
            pin_info = {
                "name": str(pin.pin_name),
                "type": str(pin.pin_type.pin_category) if hasattr(pin.pin_type, "pin_category") else "",
                "direction": "Input" if pin.direction == unreal.EdGraphPinDirection.EGPD_INPUT else "Output",
                "connections": len(pin.linked_to) if hasattr(pin, "linked_to") else 0,
            }
            pins.append(pin_info)
        info["pins"] = pins
    return info


def _graph_nodes_basic(graph):
    """그래프의 노드 기본 정보 리스트를 반환."""
    nodes = []
    for node in graph.get_editor_property("nodes"):
        if node:
            nodes.append({
                "name": node.get_name(),
                "class": node.get_class().get_name(),
            })
    return nodes


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def read_blueprint_content(
    blueprint_path,
    include_event_graph=True,
    include_functions=True,
    include_variables=True,
    include_components=True,
    include_interfaces=True,
):
    """
    Blueprint의 전체 구조를 읽는다.

    Args:
        blueprint_path: BP 에셋 전체 경로 (예: "/Game/Blueprints/BP_Test")
        include_event_graph: EventGraph 포함 여부
        include_functions: 함수 그래프 포함 여부
        include_variables: 변수 포함 여부
        include_components: SCS 컴포넌트 포함 여부
        include_interfaces: 구현 인터페이스 포함 여부

    Returns:
        dict: BP 구조 정보 또는 {"error"}
    """
    try:
        bp = _load_blueprint(blueprint_path)
        if not bp:
            return {"error": f"Failed to load blueprint: {blueprint_path}"}

        result = {
            "blueprint_path": blueprint_path,
            "blueprint_name": bp.get_name(),
            "parent_class": bp.get_editor_property("parent_class").get_name()
            if bp.get_editor_property("parent_class")
            else "None",
        }

        # Variables
        if include_variables:
            variables = []
            for var in bp.get_editor_property("new_variables"):
                var_info = {
                    "name": str(var.get_editor_property("var_name")),
                    "type": str(var.get_editor_property("var_type").get_editor_property("pin_category")),
                    "default_value": str(var.get_editor_property("default_value")),
                    "is_editable": bool(
                        var.get_editor_property("property_flags")
                        & unreal.PropertyFlags.CPF_EDIT
                    )
                    if hasattr(unreal, "PropertyFlags")
                    else False,
                }
                variables.append(var_info)
            result["variables"] = variables

        # Functions
        if include_functions:
            functions = []
            for graph in bp.get_editor_property("function_graphs"):
                if graph:
                    func_info = {
                        "name": graph.get_name(),
                        "graph_type": "Function",
                        "node_count": len(graph.get_editor_property("nodes")),
                    }
                    functions.append(func_info)
            result["functions"] = functions

        # Event graph
        if include_event_graph:
            event_graph = {}
            for graph in bp.get_editor_property("ubergraph_pages"):
                if graph and graph.get_name() == "EventGraph":
                    graph_nodes = graph.get_editor_property("nodes")
                    event_graph["name"] = graph.get_name()
                    event_graph["node_count"] = len(graph_nodes)
                    event_graph["nodes"] = _graph_nodes_basic(graph)
                    break
            result["event_graph"] = event_graph

        # Components
        if include_components:
            components = []
            scs = bp.get_editor_property("simple_construction_script")
            if scs:
                default_root = scs.get_editor_property("default_scene_root_node")
                for node in scs.get_all_nodes():
                    if node:
                        template = node.get_editor_property("component_template")
                        comp_info = {
                            "name": str(node.get_variable_name()),
                            "class": template.get_class().get_name() if template else "Unknown",
                            "is_root": node == default_root,
                        }
                        components.append(comp_info)
            result["components"] = components

        # Interfaces
        if include_interfaces:
            interfaces = []
            for iface in bp.get_editor_property("implemented_interfaces"):
                iface_class = iface.get_editor_property("interface")
                interfaces.append({
                    "name": iface_class.get_name() if iface_class else "Unknown",
                })
            result["interfaces"] = interfaces

        result["success"] = True
        return result
    except Exception as e:
        return {"error": str(e)}


def analyze_blueprint_graph(
    blueprint_path,
    graph_name="EventGraph",
    include_node_details=True,
    include_pin_connections=True,
    trace_execution_flow=True,
):
    """
    Blueprint 내 특정 그래프를 분석한다.

    Args:
        blueprint_path: BP 에셋 전체 경로
        graph_name: 그래프 이름 (기본 "EventGraph")
        include_node_details: 노드 위치 등 상세 정보 포함
        include_pin_connections: 핀/연결 정보 포함
        trace_execution_flow: 실행 흐름 추적

    Returns:
        dict: 그래프 분석 결과 또는 {"error"}
    """
    try:
        bp = _load_blueprint(blueprint_path)
        if not bp:
            return {"error": f"Failed to load blueprint: {blueprint_path}"}

        # 그래프 검색: UbergraphPages -> FunctionGraphs
        target_graph = None
        for graph in bp.get_editor_property("ubergraph_pages"):
            if graph and graph.get_name() == graph_name:
                target_graph = graph
                break
        if not target_graph:
            for graph in bp.get_editor_property("function_graphs"):
                if graph and graph.get_name() == graph_name:
                    target_graph = graph
                    break

        if not target_graph:
            return {"error": f"Graph not found: {graph_name}"}

        graph_data = {
            "graph_name": target_graph.get_name(),
            "graph_type": target_graph.get_class().get_name(),
        }

        nodes_list = []
        connections = []

        for node in target_graph.get_editor_property("nodes"):
            if not node:
                continue

            node_info = {
                "name": node.get_name(),
                "class": node.get_class().get_name(),
            }

            if include_node_details:
                node_info["pos_x"] = getattr(node, "node_pos_x", 0)
                node_info["pos_y"] = getattr(node, "node_pos_y", 0)

            if include_pin_connections and hasattr(node, "pins"):
                pin_list = []
                for pin in node.pins:
                    if not pin:
                        continue
                    pin_info = {
                        "name": str(pin.pin_name),
                        "direction": "Input" if pin.direction == unreal.EdGraphPinDirection.EGPD_INPUT else "Output",
                        "connections": len(pin.linked_to) if hasattr(pin, "linked_to") else 0,
                    }
                    pin_list.append(pin_info)

                    # 연결 기록
                    if hasattr(pin, "linked_to"):
                        for linked in pin.linked_to:
                            if linked and linked.get_owning_node():
                                connections.append({
                                    "from_node": node.get_name(),
                                    "from_pin": str(pin.pin_name),
                                    "to_node": linked.get_owning_node().get_name(),
                                    "to_pin": str(linked.pin_name),
                                })
                node_info["pins"] = pin_list

            nodes_list.append(node_info)

        graph_data["nodes"] = nodes_list
        graph_data["connections"] = connections

        return {
            "blueprint_path": blueprint_path,
            "graph_data": graph_data,
            "success": True,
        }
    except Exception as e:
        return {"error": str(e)}


def get_blueprint_variable_details(blueprint_path, variable_name=None):
    """
    Blueprint 변수의 상세 정보를 반환한다.

    Args:
        blueprint_path: BP 에셋 전체 경로
        variable_name: 특정 변수 이름 (None이면 전체)

    Returns:
        dict: 변수 상세 또는 {"error"}
    """
    try:
        bp = _load_blueprint(blueprint_path)
        if not bp:
            return {"error": f"Failed to load blueprint: {blueprint_path}"}

        variables = []
        for var in bp.get_editor_property("new_variables"):
            name = str(var.get_editor_property("var_name"))
            if variable_name and name != variable_name:
                continue

            var_type = var.get_editor_property("var_type")
            flags = var.get_editor_property("property_flags") if hasattr(var, "get_editor_property") else 0

            var_info = {
                "name": name,
                "type": str(var_type.get_editor_property("pin_category")),
                "sub_category": str(var_type.get_editor_property("pin_sub_category"))
                if hasattr(var_type, "get_editor_property")
                else "",
                "default_value": str(var.get_editor_property("default_value")),
                "friendly_name": name,
                "category": str(var.get_editor_property("category"))
                if hasattr(var, "get_editor_property")
                else "Default",
            }

            # Property flags (안전하게 처리)
            try:
                if hasattr(unreal, "PropertyFlags"):
                    var_info["is_editable"] = bool(flags & unreal.PropertyFlags.CPF_EDIT)
                    var_info["is_blueprint_visible"] = bool(flags & unreal.PropertyFlags.CPF_BLUEPRINT_VISIBLE)
                else:
                    var_info["is_editable"] = False
                    var_info["is_blueprint_visible"] = False
            except Exception:
                var_info["is_editable"] = False
                var_info["is_blueprint_visible"] = False

            # Replication
            try:
                var_info["replication"] = int(var.get_editor_property("replication_condition"))
            except Exception:
                var_info["replication"] = 0

            variables.append(var_info)

        result = {"blueprint_path": blueprint_path, "success": True}

        if variable_name:
            result["variable_name"] = variable_name
            if variables:
                result["variable"] = variables[0]
            else:
                return {"error": f"Variable not found: {variable_name}"}
        else:
            result["variables"] = variables
            result["variable_count"] = len(variables)

        return result
    except Exception as e:
        return {"error": str(e)}


def get_blueprint_function_details(blueprint_path, function_name=None, include_graph=True):
    """
    Blueprint 함수의 상세 정보를 반환한다.

    Args:
        blueprint_path: BP 에셋 전체 경로
        function_name: 특정 함수 이름 (None이면 전체)
        include_graph: 함수 그래프 노드 포함 여부

    Returns:
        dict: 함수 상세 또는 {"error"}
    """
    try:
        bp = _load_blueprint(blueprint_path)
        if not bp:
            return {"error": f"Failed to load blueprint: {blueprint_path}"}

        functions = []
        for graph in bp.get_editor_property("function_graphs"):
            if not graph:
                continue
            name = graph.get_name()
            if function_name and name != function_name:
                continue

            func_info = {
                "name": name,
                "graph_type": "Function",
                "node_count": len(graph.get_editor_property("nodes")),
            }

            # 함수 시그니처 분석: FunctionEntry / FunctionResult 노드에서 핀 추출
            input_params = []
            output_params = []

            for node in graph.get_editor_property("nodes"):
                if not node:
                    continue
                cls_name = node.get_class().get_name()

                if "FunctionEntry" in cls_name:
                    if hasattr(node, "pins"):
                        for pin in node.pins:
                            if (
                                pin
                                and pin.direction == unreal.EdGraphPinDirection.EGPD_OUTPUT
                                and str(pin.pin_name) != "then"
                            ):
                                input_params.append({
                                    "name": str(pin.pin_name),
                                    "type": str(pin.pin_type.pin_category)
                                    if hasattr(pin.pin_type, "pin_category")
                                    else "",
                                })

                elif "FunctionResult" in cls_name:
                    if hasattr(node, "pins"):
                        for pin in node.pins:
                            if (
                                pin
                                and pin.direction == unreal.EdGraphPinDirection.EGPD_INPUT
                                and str(pin.pin_name) != "exec"
                            ):
                                output_params.append({
                                    "name": str(pin.pin_name),
                                    "type": str(pin.pin_type.pin_category)
                                    if hasattr(pin.pin_type, "pin_category")
                                    else "",
                                })

            func_info["input_parameters"] = input_params
            func_info["output_parameters"] = output_params

            if include_graph:
                func_info["graph_nodes"] = _graph_nodes_basic(graph)

            functions.append(func_info)

        result = {"blueprint_path": blueprint_path, "success": True}

        if function_name:
            result["function_name"] = function_name
            if functions:
                result["function"] = functions[0]
            else:
                return {"error": f"Function not found: {function_name}"}
        else:
            result["functions"] = functions
            result["function_count"] = len(functions)

        return result
    except Exception as e:
        return {"error": str(e)}
