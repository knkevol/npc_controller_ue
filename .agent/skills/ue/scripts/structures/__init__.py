"""
Structures Sub-package
======================
구조물 생성의 공통 빌딩 블록.
MCP의 safe_spawn_actor() TCP 호출을 UE5 Python API 직접 호출로 대체.
"""

import unreal


def spawn_static_mesh_actor(
    name,
    location,
    scale=None,
    mesh_path="/Engine/BasicShapes/Cube.Cube",
    rotation=None,
):
    """단일 StaticMeshActor를 스폰하고 메시를 설정한다.

    모든 구조물 생성 함수(pyramid, wall, tower 등)의 기본 빌딩 블록.
    MCP의 safe_spawn_actor() 에 대응.

    Args:
        name (str): 액터 라벨 이름.
        location (list[float]): [x, y, z] 위치.
        scale (list[float], optional): [x, y, z] 스케일. 기본 [1, 1, 1].
        mesh_path (str): 스태틱 메시 에셋 경로.
        rotation (list[float], optional): [pitch, yaw, roll] 회전.

    Returns:
        unreal.StaticMeshActor: 스폰된 액터. 실패 시 None.
    """
    loc = unreal.Vector(location[0], location[1], location[2])
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, loc
    )
    if actor is None:
        return None

    actor.set_actor_label(name)

    if scale is not None:
        actor.set_actor_scale3d(unreal.Vector(scale[0], scale[1], scale[2]))

    if rotation is not None:
        actor.set_actor_rotation(
            unreal.Rotator(rotation[0], rotation[1], rotation[2]), False
        )

    mesh_comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if mesh_comp is not None:
        mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
        if mesh is not None:
            mesh_comp.set_static_mesh(mesh)

    return actor


def batch_spawn(specs, mesh_path="/Engine/BasicShapes/Cube.Cube"):
    """여러 StaticMeshActor를 일괄 스폰한다.

    Args:
        specs (list[dict]): [{"name": ..., "location": [...], "scale": [...], "rotation": [...]}, ...]
        mesh_path (str): 공통 메시 경로.

    Returns:
        list[str]: 스폰된 액터 이름 목록.
    """
    spawned = []
    for spec in specs:
        actor = spawn_static_mesh_actor(
            name=spec["name"],
            location=spec["location"],
            scale=spec.get("scale"),
            mesh_path=spec.get("mesh", mesh_path),
            rotation=spec.get("rotation"),
        )
        if actor is not None:
            spawned.append(actor.get_name())
    return spawned
