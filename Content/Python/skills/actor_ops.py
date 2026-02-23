"""
Actor Operations
================
레벨 내 액터 조회, 검색, 삭제, 트랜스폼 설정.
MCP의 get_actors_in_level / find_actors_by_name / delete_actor / set_actor_transform에 대응.
"""

import unreal
import fnmatch


def get_actors_in_level():
    """레벨 내 모든 액터 목록을 반환한다.

    Returns:
        dict: {"actors": [{"name": ..., "label": ..., "class": ..., "location": [...], "rotation": [...], "scale": [...]}, ...]}
    """
    try:
        actors = unreal.EditorLevelLibrary.get_all_level_actors()
        result = []
        for a in actors:
            if a is None:
                continue
            loc = a.get_actor_location()
            rot = a.get_actor_rotation()
            scale = a.get_actor_scale3d()
            result.append({
                "name": a.get_name(),
                "label": a.get_actor_label(),
                "class": a.get_class().get_name(),
                "location": [loc.x, loc.y, loc.z],
                "rotation": [rot.pitch, rot.yaw, rot.roll],
                "scale": [scale.x, scale.y, scale.z],
            })
        return {"actors": result}
    except Exception as e:
        return {"error": str(e)}


def find_actors_by_name(pattern):
    """이름 패턴으로 액터를 검색한다.

    C++ MCP는 단순 Contains 매칭을 사용하지만,
    여기서는 fnmatch 와일드카드도 지원한다.
    패턴에 *나 ?가 없으면 Contains 매칭으로 동작.

    Args:
        pattern (str): 검색 패턴. "Wall" → 이름에 Wall 포함. "Wall*" → fnmatch.

    Returns:
        dict: {"actors": [...]}
    """
    try:
        actors = unreal.EditorLevelLibrary.get_all_level_actors()
        use_glob = ("*" in pattern or "?" in pattern)
        result = []
        for a in actors:
            if a is None:
                continue
            name = a.get_name()
            matched = False
            if use_glob:
                matched = fnmatch.fnmatch(name, pattern)
            else:
                matched = pattern in name
            if matched:
                loc = a.get_actor_location()
                rot = a.get_actor_rotation()
                scale = a.get_actor_scale3d()
                result.append({
                    "name": name,
                    "label": a.get_actor_label(),
                    "class": a.get_class().get_name(),
                    "location": [loc.x, loc.y, loc.z],
                    "rotation": [rot.pitch, rot.yaw, rot.roll],
                    "scale": [scale.x, scale.y, scale.z],
                })
        return {"actors": result}
    except Exception as e:
        return {"error": str(e)}


def delete_actor(name):
    """이름으로 액터를 찾아 삭제한다.

    Args:
        name (str): 삭제할 액터의 내부 이름 (get_name() 결과).

    Returns:
        dict: {"deleted_actor": {...}} 또는 {"error": "..."}
    """
    try:
        actors = unreal.EditorLevelLibrary.get_all_level_actors()
        for a in actors:
            if a is None:
                continue
            if a.get_name() == name:
                loc = a.get_actor_location()
                info = {
                    "name": a.get_name(),
                    "label": a.get_actor_label(),
                    "class": a.get_class().get_name(),
                    "location": [loc.x, loc.y, loc.z],
                }
                a.destroy_actor()
                return {"deleted_actor": info}
        return {"error": f"Actor not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def set_actor_transform(name, location=None, rotation=None, scale=None):
    """액터의 트랜스폼(위치/회전/스케일)을 설정한다.

    Args:
        name (str): 액터의 내부 이름.
        location (list[float], optional): [x, y, z] 위치.
        rotation (list[float], optional): [pitch, yaw, roll] 회전.
        scale (list[float], optional): [x, y, z] 스케일.

    Returns:
        dict: 변경 후 트랜스폼 정보 또는 {"error": "..."}
    """
    try:
        actors = unreal.EditorLevelLibrary.get_all_level_actors()
        target = None
        for a in actors:
            if a is not None and a.get_name() == name:
                target = a
                break

        if target is None:
            return {"error": f"Actor not found: {name}"}

        if location is not None:
            target.set_actor_location(
                unreal.Vector(location[0], location[1], location[2]),
                False, False
            )

        if rotation is not None:
            target.set_actor_rotation(
                unreal.Rotator(rotation[0], rotation[1], rotation[2]),
                False
            )

        if scale is not None:
            target.set_actor_scale3d(
                unreal.Vector(scale[0], scale[1], scale[2])
            )

        loc = target.get_actor_location()
        rot = target.get_actor_rotation()
        sc = target.get_actor_scale3d()
        return {
            "name": target.get_name(),
            "label": target.get_actor_label(),
            "class": target.get_class().get_name(),
            "location": [loc.x, loc.y, loc.z],
            "rotation": [rot.pitch, rot.yaw, rot.roll],
            "scale": [sc.x, sc.y, sc.z],
        }
    except Exception as e:
        return {"error": str(e)}
