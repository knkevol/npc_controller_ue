"""
Blueprint Core Operations
=========================
BP 생성, 컴포넌트 추가, 메시/물리 설정, 컴파일.
MCP의 5개 BP 도구를 UE5 Python API로 직접 구현.
"""
import unreal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_blueprint(blueprint_name, base_path="/Game/Blueprints"):
    """이름으로 Blueprint 에셋을 로드. 전체 경로 또는 이름만 전달 가능."""
    # 전체 경로인 경우 그대로 로드
    if blueprint_name.startswith("/"):
        asset = unreal.EditorAssetLibrary.load_asset(blueprint_name)
        if asset and isinstance(asset, unreal.Blueprint):
            return asset
        return None

    # 이름만 주어진 경우 base_path에서 검색
    asset_path = f"{base_path}/{blueprint_name}"
    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    if asset and isinstance(asset, unreal.Blueprint):
        return asset

    # base_path 하위 재귀 검색
    all_assets = unreal.EditorAssetLibrary.list_assets(base_path, recursive=True)
    for p in all_assets:
        if p.endswith(f"/{blueprint_name}") or p.endswith(f"/{blueprint_name}.{blueprint_name}"):
            asset = unreal.EditorAssetLibrary.load_asset(p)
            if asset and isinstance(asset, unreal.Blueprint):
                return asset
    return None


def _find_scs_node(bp, component_name):
    """SCS에서 component_name에 해당하는 노드를 반환."""
    scs = bp.get_editor_property("simple_construction_script")
    if not scs:
        return None
    for node in scs.get_all_nodes():
        if node and node.get_variable_name() == component_name:
            return node
    return None


def _resolve_parent_class(parent_class_name):
    """parent_class 이름을 UClass 객체로 변환."""
    # 일반적인 내장 클래스 매핑
    builtin = {
        "Actor": unreal.Actor,
        "Pawn": unreal.Pawn,
        "Character": unreal.Character,
    }
    cls_obj = builtin.get(parent_class_name)
    if cls_obj:
        return cls_obj.static_class()

    # ClassIterator로 커스텀 클래스 검색
    # "A" 접두어 없이도 검색 가능하도록 양쪽 시도
    search_names = [parent_class_name]
    if not parent_class_name.startswith("A"):
        search_names.append("A" + parent_class_name)

    for cls in unreal.ClassIterator(unreal.Actor):
        name = cls.get_name()
        if name in search_names:
            return cls
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_blueprint(name, parent_class="Actor", path="/Game/Blueprints"):
    """
    새 Blueprint 클래스를 생성한다.

    Args:
        name: Blueprint 에셋 이름
        parent_class: 부모 클래스 이름 (기본 "Actor")
        path: 저장 경로 (기본 "/Game/Blueprints")

    Returns:
        dict: {"name", "path"} 또는 {"error"}
    """
    try:
        asset_path = f"{path}/{name}"
        if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
            return {"error": f"Blueprint already exists: {name}"}

        parent = _resolve_parent_class(parent_class)
        if not parent:
            return {"error": f"Parent class not found: {parent_class}"}

        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", parent)

        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        bp = asset_tools.create_asset(name, path, unreal.Blueprint, factory)
        if not bp:
            return {"error": f"Failed to create blueprint: {name}"}

        unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False)
        return {
            "name": name,
            "path": asset_path,
            "parent_class": bp.get_editor_property("parent_class").get_name(),
        }
    except Exception as e:
        return {"error": str(e)}


def add_component_to_blueprint(
    blueprint_name,
    component_type,
    component_name,
    location=None,
    rotation=None,
    scale=None,
    component_properties=None,
):
    """
    Blueprint에 컴포넌트를 추가한다.

    Args:
        blueprint_name: BP 이름 또는 경로
        component_type: 컴포넌트 클래스 이름 (예: "StaticMeshComponent")
        component_name: 추가할 컴포넌트의 변수 이름
        location: [x, y, z] 상대 위치 (선택)
        rotation: [pitch, yaw, roll] 상대 회전 (선택)
        scale: [x, y, z] 상대 스케일 (선택)
        component_properties: 추가 프로퍼티 dict (선택)

    Returns:
        dict: {"component_name", "component_type"} 또는 {"error"}
    """
    try:
        bp = _find_blueprint(blueprint_name)
        if not bp:
            return {"error": f"Blueprint not found: {blueprint_name}"}

        # 컴포넌트 클래스 검색
        comp_class = _resolve_component_class(component_type)
        if not comp_class:
            return {"error": f"Unknown component type: {component_type}"}

        scs = bp.get_editor_property("simple_construction_script")
        if not scs:
            return {"error": "Blueprint has no SimpleConstructionScript"}

        node = scs.create_node(comp_class, component_name)
        if not node:
            return {"error": f"Failed to create SCS node for {component_type}"}

        # 트랜스폼 설정
        template = node.get_editor_property("component_template")
        if template and isinstance(template, unreal.SceneComponent):
            if location and len(location) >= 3:
                template.set_relative_location(
                    unreal.Vector(location[0], location[1], location[2])
                )
            if rotation and len(rotation) >= 3:
                template.set_relative_rotation(
                    unreal.Rotator(rotation[0], rotation[1], rotation[2])
                )
            if scale and len(scale) >= 3:
                template.set_relative_scale3d(
                    unreal.Vector(scale[0], scale[1], scale[2])
                )

        scs.add_node(node)

        # 컴파일
        unreal.KismetEditorUtilities.compile_blueprint(bp)

        return {
            "component_name": component_name,
            "component_type": component_type,
        }
    except Exception as e:
        return {"error": str(e)}


def set_static_mesh_properties(
    blueprint_name,
    component_name,
    static_mesh="/Engine/BasicShapes/Cube.Cube",
):
    """
    StaticMeshComponent에 메시를 설정한다.

    Args:
        blueprint_name: BP 이름 또는 경로
        component_name: 대상 컴포넌트 변수 이름
        static_mesh: 메시 에셋 경로

    Returns:
        dict: {"component"} 또는 {"error"}
    """
    try:
        bp = _find_blueprint(blueprint_name)
        if not bp:
            return {"error": f"Blueprint not found: {blueprint_name}"}

        node = _find_scs_node(bp, component_name)
        if not node:
            return {"error": f"Component not found: {component_name}"}

        template = node.get_editor_property("component_template")
        if not isinstance(template, unreal.StaticMeshComponent):
            return {"error": "Component is not a StaticMeshComponent"}

        mesh = unreal.EditorAssetLibrary.load_asset(static_mesh)
        if not mesh:
            return {"error": f"Failed to load mesh: {static_mesh}"}

        template.set_static_mesh(mesh)
        unreal.BlueprintEditorLibrary.mark_blueprint_as_modified(bp) if hasattr(unreal, "BlueprintEditorLibrary") else None

        return {"component": component_name}
    except Exception as e:
        return {"error": str(e)}


def set_physics_properties(
    blueprint_name,
    component_name,
    simulate_physics=True,
    gravity_enabled=True,
    mass=1.0,
    linear_damping=0.01,
    angular_damping=0.0,
):
    """
    PrimitiveComponent에 물리 속성을 설정한다.

    Args:
        blueprint_name: BP 이름 또는 경로
        component_name: 대상 컴포넌트 변수 이름
        simulate_physics: 물리 시뮬레이션 활성화
        gravity_enabled: 중력 활성화
        mass: 질량 (kg)
        linear_damping: 선형 감쇠
        angular_damping: 각도 감쇠

    Returns:
        dict: {"component"} 또는 {"error"}
    """
    try:
        bp = _find_blueprint(blueprint_name)
        if not bp:
            return {"error": f"Blueprint not found: {blueprint_name}"}

        node = _find_scs_node(bp, component_name)
        if not node:
            return {"error": f"Component not found: {component_name}"}

        template = node.get_editor_property("component_template")
        if not isinstance(template, unreal.PrimitiveComponent):
            return {"error": "Component is not a PrimitiveComponent"}

        template.set_simulate_physics(simulate_physics)
        template.set_enable_gravity(gravity_enabled)
        template.set_mass_override_in_kg(unreal.Name("None"), mass)
        template.set_linear_damping(linear_damping)
        template.set_angular_damping(angular_damping)

        return {"component": component_name}
    except Exception as e:
        return {"error": str(e)}


def compile_blueprint(blueprint_name):
    """
    Blueprint를 컴파일한다.

    Args:
        blueprint_name: BP 이름 또는 경로

    Returns:
        dict: {"name", "compiled": True} 또는 {"error"}
    """
    try:
        bp = _find_blueprint(blueprint_name)
        if not bp:
            return {"error": f"Blueprint not found: {blueprint_name}"}

        unreal.KismetEditorUtilities.compile_blueprint(bp)
        return {"name": blueprint_name, "compiled": True}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_component_class(component_type):
    """컴포넌트 타입 이름을 UClass로 변환."""
    # 일반적 매핑
    known = {
        "StaticMeshComponent": unreal.StaticMeshComponent,
        "BoxComponent": unreal.BoxComponent,
        "SphereComponent": unreal.SphereComponent,
        "CapsuleComponent": unreal.CapsuleComponent,
        "SceneComponent": unreal.SceneComponent,
        "SkeletalMeshComponent": unreal.SkeletalMeshComponent,
        "AudioComponent": unreal.AudioComponent,
        "PointLightComponent": unreal.PointLightComponent,
        "SpotLightComponent": unreal.SpotLightComponent,
        "DirectionalLightComponent": unreal.DirectionalLightComponent,
        "ParticleSystemComponent": unreal.ParticleSystemComponent,
        "ArrowComponent": unreal.ArrowComponent,
        "BillboardComponent": unreal.BillboardComponent,
        "TextRenderComponent": unreal.TextRenderComponent,
        "DecalComponent": unreal.DecalComponent,
    }

    # 정확 매칭
    cls = known.get(component_type)
    if cls:
        return cls.static_class()

    # "Component" 접미사 없이 시도
    if not component_type.endswith("Component"):
        cls = known.get(component_type + "Component")
        if cls:
            return cls.static_class()

    # ClassIterator로 동적 검색
    search_names = [component_type]
    if not component_type.startswith("U"):
        search_names.append("U" + component_type)
    if not component_type.endswith("Component"):
        search_names.append(component_type + "Component")
        if not component_type.startswith("U"):
            search_names.append("U" + component_type + "Component")

    for cls_iter in unreal.ClassIterator(unreal.ActorComponent):
        name = cls_iter.get_name()
        if name in search_names:
            return cls_iter
    return None
