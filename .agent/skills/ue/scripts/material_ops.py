"""
material_ops.py - Material Operations Skill Set
=================================================
MCP의 머티리얼 도구 5종을 UE5 Python API로 포팅.

함수 목록:
- get_available_materials()
- apply_material_to_actor()
- apply_material_to_blueprint()
- get_actor_material_info()
- set_mesh_material_color()
"""

import unreal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_actor_by_name(actor_name):
    """에디터 월드에서 이름으로 액터를 찾는다."""
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = subsystem.get_all_level_actors()
    for actor in actors:
        if actor.get_name() == actor_name:
            return actor
    return None


def _find_blueprint(blueprint_name):
    """이름으로 블루프린트 에셋을 찾는다. /Game/ 아래에서 재귀 검색."""
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    ar_filter = unreal.ARFilter()
    ar_filter.class_paths = [unreal.TopLevelAssetPath("/Script/Engine", "Blueprint")]
    ar_filter.recursive_paths = True
    ar_filter.package_paths = ["/Game/"]

    assets = registry.get_assets(ar_filter)
    for asset_data in assets:
        if asset_data.asset_name == blueprint_name:
            asset = asset_data.get_asset()
            if asset and isinstance(asset, unreal.Blueprint):
                return asset
    return None


def _get_scs_component(blueprint, component_name):
    """블루프린트의 SimpleConstructionScript에서 컴포넌트 노드를 찾는다."""
    scs = blueprint.simple_construction_script
    if not scs:
        return None
    for node in scs.get_all_nodes():
        if node and node.get_variable_name() == component_name:
            return node.component_template
    return None


# ---------------------------------------------------------------------------
# 1. get_available_materials
# ---------------------------------------------------------------------------

def get_available_materials(search_path="/Game/", include_engine_materials=True):
    """
    프로젝트에서 사용 가능한 머티리얼 목록을 검색한다.

    Args:
        search_path: 검색 경로 (기본: "/Game/")
        include_engine_materials: 엔진 머티리얼 포함 여부 (기본: True)

    Returns:
        dict: materials 리스트, count, search_path_used
    """
    try:
        registry = unreal.AssetRegistryHelpers.get_asset_registry()

        package_paths = []
        if search_path:
            path = search_path if search_path.startswith("/") else "/" + search_path
            if not path.endswith("/"):
                path += "/"
            package_paths.append(path)
        else:
            package_paths.append("/Game/")

        if include_engine_materials:
            package_paths.append("/Engine/")

        ar_filter = unreal.ARFilter()
        ar_filter.class_paths = [
            unreal.TopLevelAssetPath("/Script/Engine", "MaterialInterface"),
            unreal.TopLevelAssetPath("/Script/Engine", "Material"),
            unreal.TopLevelAssetPath("/Script/Engine", "MaterialInstanceConstant"),
        ]
        ar_filter.package_paths = package_paths
        ar_filter.recursive_paths = True

        assets = registry.get_assets(ar_filter)

        materials = []
        for asset_data in assets:
            materials.append({
                "name": str(asset_data.asset_name),
                "path": str(asset_data.get_full_name()),
                "package": str(asset_data.package_name),
                "class": str(asset_data.asset_class_path.asset_name) if hasattr(asset_data, 'asset_class_path') else "",
            })

        return {
            "materials": materials,
            "count": len(materials),
            "search_path_used": search_path if search_path else "/Game/",
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# 2. apply_material_to_actor
# ---------------------------------------------------------------------------

def apply_material_to_actor(actor_name, material_path, material_slot=0):
    """
    레벨의 액터에 머티리얼을 적용한다.

    Args:
        actor_name: 대상 액터 이름
        material_path: 머티리얼 에셋 경로 (예: "/Engine/BasicShapes/BasicShapeMaterial")
        material_slot: 머티리얼 슬롯 인덱스 (기본: 0)

    Returns:
        dict: 성공 여부와 적용 정보
    """
    try:
        actor = _find_actor_by_name(actor_name)
        if not actor:
            return {"error": f"Actor not found: {actor_name}"}

        material = unreal.EditorAssetLibrary.load_asset(material_path)
        if not material or not isinstance(material, unreal.MaterialInterface):
            return {"error": f"Failed to load material: {material_path}"}

        components = actor.get_components_by_class(unreal.StaticMeshComponent)
        if not components:
            return {"error": "No mesh components found on actor"}

        applied = False
        for comp in components:
            comp.set_material(material_slot, material)
            applied = True

        if not applied:
            return {"error": "Failed to apply material to any component"}

        return {
            "success": True,
            "actor_name": actor_name,
            "material_path": material_path,
            "material_slot": material_slot,
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# 3. apply_material_to_blueprint
# ---------------------------------------------------------------------------

def apply_material_to_blueprint(blueprint_name, component_name, material_path, material_slot=0):
    """
    블루프린트의 컴포넌트에 머티리얼을 적용한다.

    Args:
        blueprint_name: 블루프린트 이름
        component_name: 컴포넌트 이름
        material_path: 머티리얼 에셋 경로
        material_slot: 머티리얼 슬롯 인덱스 (기본: 0)

    Returns:
        dict: 성공 여부와 적용 정보
    """
    try:
        blueprint = _find_blueprint(blueprint_name)
        if not blueprint:
            return {"error": f"Blueprint not found: {blueprint_name}"}

        component = _get_scs_component(blueprint, component_name)
        if not component:
            return {"error": f"Component not found: {component_name}"}

        if not isinstance(component, unreal.PrimitiveComponent):
            return {"error": "Component is not a primitive component"}

        material = unreal.EditorAssetLibrary.load_asset(material_path)
        if not material or not isinstance(material, unreal.MaterialInterface):
            return {"error": f"Failed to load material: {material_path}"}

        component.set_material(material_slot, material)

        unreal.KismetSystemLibrary.flush_persistent_debug_lines(None)

        return {
            "success": True,
            "blueprint_name": blueprint_name,
            "component_name": component_name,
            "material_path": material_path,
            "material_slot": material_slot,
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# 4. get_actor_material_info
# ---------------------------------------------------------------------------

def get_actor_material_info(actor_name):
    """
    액터에 적용된 머티리얼 정보를 가져온다.

    Args:
        actor_name: 대상 액터 이름

    Returns:
        dict: actor_name, material_slots 리스트, total_slots
    """
    try:
        actor = _find_actor_by_name(actor_name)
        if not actor:
            return {"error": f"Actor not found: {actor_name}"}

        components = actor.get_components_by_class(unreal.StaticMeshComponent)
        material_slots = []

        for comp in components:
            num_materials = comp.get_num_materials()
            for i in range(num_materials):
                mat = comp.get_material(i)
                slot_info = {
                    "slot": i,
                    "component": comp.get_name(),
                }
                if mat:
                    slot_info["material_name"] = mat.get_name()
                    slot_info["material_path"] = mat.get_path_name()
                    slot_info["material_class"] = mat.get_class().get_name()
                else:
                    slot_info["material_name"] = "None"
                    slot_info["material_path"] = ""
                    slot_info["material_class"] = ""
                material_slots.append(slot_info)

        return {
            "actor_name": actor_name,
            "material_slots": material_slots,
            "total_slots": len(material_slots),
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# 5. set_mesh_material_color
# ---------------------------------------------------------------------------

def set_mesh_material_color(blueprint_name, component_name, color,
                            material_path="/Engine/BasicShapes/BasicShapeMaterial",
                            parameter_name="BaseColor", material_slot=0):
    """
    블루프린트 메시 컴포넌트에 동적 머티리얼 인스턴스를 생성하고 색상을 설정한다.

    Args:
        blueprint_name: 블루프린트 이름
        component_name: 컴포넌트 이름
        color: [R, G, B, A] 또는 [R, G, B] (0.0-1.0)
        material_path: 베이스 머티리얼 경로
        parameter_name: 색상 파라미터 이름 (기본: "BaseColor")
        material_slot: 머티리얼 슬롯 인덱스 (기본: 0)

    Returns:
        dict: 성공 여부와 적용 정보
    """
    try:
        if not isinstance(color, (list, tuple)) or len(color) < 3:
            return {"error": "Invalid color format. Must be [R, G, B] or [R, G, B, A]."}

        r = max(0.0, min(1.0, float(color[0])))
        g = max(0.0, min(1.0, float(color[1])))
        b = max(0.0, min(1.0, float(color[2])))
        a = max(0.0, min(1.0, float(color[3]))) if len(color) >= 4 else 1.0

        blueprint = _find_blueprint(blueprint_name)
        if not blueprint:
            return {"error": f"Blueprint not found: {blueprint_name}"}

        component = _get_scs_component(blueprint, component_name)
        if not component:
            return {"error": f"Component not found: {component_name}"}

        if not isinstance(component, unreal.PrimitiveComponent):
            return {"error": "Component is not a primitive component"}

        # Load base material
        if material_path:
            base_material = unreal.EditorAssetLibrary.load_asset(material_path)
        else:
            base_material = component.get_material(material_slot)

        if not base_material:
            base_material = unreal.EditorAssetLibrary.load_asset(
                "/Engine/BasicShapes/BasicShapeMaterial"
            )

        if not base_material or not isinstance(base_material, unreal.MaterialInterface):
            return {"error": "No valid material found"}

        # Create dynamic material instance
        dyn_material = unreal.MaterialInstanceDynamic.create(base_material, component)
        if not dyn_material:
            return {"error": "Failed to create dynamic material instance"}

        # Set color parameter
        linear_color = unreal.LinearColor(r=r, g=g, b=b, a=a)
        dyn_material.set_vector_parameter_value(parameter_name, linear_color)

        # Apply to component
        component.set_material(material_slot, dyn_material)

        return {
            "success": True,
            "component": component_name,
            "material_slot": material_slot,
            "parameter_name": parameter_name,
            "color": [r, g, b, a],
        }
    except Exception as e:
        return {"error": str(e)}
