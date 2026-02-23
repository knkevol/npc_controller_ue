"""
Physics Actor
==============
물리 시뮬레이션이 적용된 액터를 BP 생성 → 컴포넌트 추가 → 물리 설정 → 컴파일 → 스폰하는 워크플로우.
MCP의 spawn_physics_blueprint_actor에 대응.
"""

import unreal


def spawn_physics_blueprint_actor(
    name,
    mesh_path="/Engine/BasicShapes/Cube.Cube",
    location=None,
    scale=None,
    color=None,
    simulate_physics=True,
    gravity_enabled=True,
    mass=1.0,
):
    """물리가 적용된 BP 액터를 생성하여 레벨에 스폰한다.

    워크플로우:
      1. Blueprint 생성 (parent: Actor)
      2. StaticMeshComponent 추가 + 메시 설정
      3. 물리 프로퍼티 설정
      4. (옵션) 색상 설정
      5. 컴파일
      6. 레벨에 스폰

    Args:
        name (str): 액터 이름. BP 이름은 "{name}_BP".
        mesh_path (str): 스태틱 메시 에셋 경로.
        location (list[float], optional): [x, y, z]. 기본 [0, 0, 0].
        scale (list[float], optional): [x, y, z]. 기본 [1, 1, 1].
        color (list[float], optional): [R, G, B] 또는 [R, G, B, A]. 0.0-1.0.
        simulate_physics (bool): 물리 시뮬레이션 활성화.
        gravity_enabled (bool): 중력 활성화.
        mass (float): 질량(kg).

    Returns:
        dict: {"name": ..., "blueprint": ..., "location": [...]} 또는 {"error": "..."}
    """
    if location is None:
        location = [0.0, 0.0, 0.0]
    if scale is None:
        scale = [1.0, 1.0, 1.0]

    bp_name = f"{name}_BP"
    bp_path = f"/Game/Blueprints/{bp_name}"
    component_name = "Mesh"

    try:
        # 1. Blueprint 생성
        if unreal.EditorAssetLibrary.does_asset_exist(bp_path):
            bp = unreal.EditorAssetLibrary.load_asset(bp_path)
        else:
            factory = unreal.BlueprintFactory()
            factory.set_editor_property("parent_class", unreal.Actor)
            asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
            bp = asset_tools.create_asset(bp_name, "/Game/Blueprints", unreal.Blueprint, factory)
            if bp is None:
                return {"error": f"Failed to create blueprint: {bp_name}"}

        # 2. StaticMeshComponent 추가
        scs = bp.get_editor_property("simple_construction_script")
        comp_class = unreal.StaticMeshComponent.static_class()
        node = scs.create_node(comp_class, component_name)
        if node is None:
            return {"error": f"Failed to create component node: {component_name}"}

        scs.add_node(node)

        # 컴포넌트 템플릿에 접근
        comp_template = node.get_editor_property("component_template")
        scene_comp = unreal.SceneComponent.cast(comp_template) if hasattr(unreal.SceneComponent, 'cast') else comp_template

        # 스케일 설정
        if hasattr(comp_template, "set_editor_property"):
            comp_template.set_editor_property("relative_scale3d", unreal.Vector(*scale))

        # 3. 메시 설정
        mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
        if mesh is not None:
            comp_template.set_static_mesh(mesh)

        # 4. 물리 설정
        comp_template.set_simulate_physics(simulate_physics)
        if hasattr(comp_template, "set_enable_gravity"):
            comp_template.set_enable_gravity(gravity_enabled)
        if mass != 1.0:
            comp_template.set_mass_override_in_kg(unreal.Name("None"), mass)

        # 5. 색상 설정
        if color is not None:
            if len(color) == 3:
                color = color + [1.0]
            if len(color) == 4:
                mat = unreal.EditorAssetLibrary.load_asset(
                    "/Engine/BasicShapes/BasicShapeMaterial"
                )
                if mat is not None:
                    mid = unreal.MaterialInstanceDynamic.create(mat, comp_template)
                    if mid is not None:
                        mid.set_vector_parameter_value(
                            "BaseColor",
                            unreal.LinearColor(color[0], color[1], color[2], color[3]),
                        )
                        comp_template.set_material(0, mid)

        # 6. 컴파일
        unreal.KismetEditorUtilities.compile_blueprint(bp)

        # 7. 스폰
        world = unreal.EditorLevelLibrary.get_editor_world()
        if world is None:
            return {"error": "Failed to get editor world"}

        generated_class = bp.get_editor_property("generated_class")
        if generated_class is None:
            return {"error": "Blueprint has no generated class after compilation"}

        spawn_loc = unreal.Vector(location[0], location[1], location[2])
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            generated_class, spawn_loc
        )

        if actor is None:
            return {"error": f"Failed to spawn actor from blueprint: {bp_name}"}

        actor.set_actor_label(name)
        if scale != [1.0, 1.0, 1.0]:
            actor.set_actor_scale3d(unreal.Vector(scale[0], scale[1], scale[2]))

        loc = actor.get_actor_location()
        return {
            "name": actor.get_name(),
            "label": name,
            "blueprint": bp_path,
            "location": [loc.x, loc.y, loc.z],
            "scale": scale,
        }

    except Exception as e:
        return {"error": str(e)}
