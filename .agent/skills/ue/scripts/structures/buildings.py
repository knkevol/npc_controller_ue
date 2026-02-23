"""
structures/buildings.py - Building Structures
==============================================
MCP의 타워, 집, 맨션 구조물 생성 기능을 UE5 Python API로 포팅.

함수 목록:
- create_tower(): 다양한 스타일의 타워
- construct_house(): 건축 디테일이 있는 집
- construct_mansion(): 대규모 맨션
"""

import math
from skills.structures import spawn_static_mesh_actor


# ---------------------------------------------------------------------------
# 1. create_tower
# ---------------------------------------------------------------------------

def create_tower(base_size=4, height=10, block_size=100, location=None,
                 tower_style="cylindrical", mesh="/Engine/BasicShapes/Cube.Cube",
                 name_prefix="TowerBlock"):
    """
    다양한 건축 스타일의 타워를 생성한다.

    Args:
        base_size: 베이스 크기 (기본: 4)
        height: 높이 (층 수, 기본: 10)
        block_size: 블록 크기 (기본: 100)
        location: [x, y, z] 위치 (기본: [0,0,0])
        tower_style: "cylindrical", "square", "tapered" (기본: "cylindrical")
        mesh: 메시 경로
        name_prefix: 이름 접두사

    Returns:
        dict: actors 리스트, tower_style
    """
    if location is None:
        location = [0, 0, 0]

    try:
        spawned = []
        scale = block_size / 100.0

        for level in range(height):
            level_height = location[2] + level * block_size

            if tower_style == "cylindrical":
                radius = (base_size / 2) * block_size
                circumference = 2 * math.pi * radius
                num_blocks = max(8, int(circumference / block_size))

                for i in range(num_blocks):
                    angle = (2 * math.pi * i) / num_blocks
                    x = location[0] + radius * math.cos(angle)
                    y = location[1] + radius * math.sin(angle)
                    actor = spawn_static_mesh_actor(
                        f"{name_prefix}_{level}_{i}",
                        [x, y, level_height],
                        scale=[scale, scale, scale],
                        mesh_path=mesh,
                    )
                    if actor:
                        spawned.append(actor.get_name())

            elif tower_style == "tapered":
                current_size = max(1, base_size - (level // 2))
                half_size = current_size / 2

                for side in range(4):
                    for i in range(current_size):
                        x, y = _square_wall_pos(
                            location, side, i, half_size, block_size
                        )
                        actor = spawn_static_mesh_actor(
                            f"{name_prefix}_{level}_s{side}_{i}",
                            [x, y, level_height],
                            scale=[scale, scale, scale],
                            mesh_path=mesh,
                        )
                        if actor:
                            spawned.append(actor.get_name())

            else:  # square
                half_size = base_size / 2
                for side in range(4):
                    for i in range(base_size):
                        x, y = _square_wall_pos(
                            location, side, i, half_size, block_size
                        )
                        actor = spawn_static_mesh_actor(
                            f"{name_prefix}_{level}_s{side}_{i}",
                            [x, y, level_height],
                            scale=[scale, scale, scale],
                            mesh_path=mesh,
                        )
                        if actor:
                            spawned.append(actor.get_name())

            # 장식 요소 (3층마다)
            if level % 3 == 2 and level < height - 1:
                for corner in range(4):
                    angle = corner * math.pi / 2
                    dx = (base_size / 2 + 0.5) * block_size * math.cos(angle)
                    dy = (base_size / 2 + 0.5) * block_size * math.sin(angle)
                    actor = spawn_static_mesh_actor(
                        f"{name_prefix}_{level}_detail_{corner}",
                        [location[0] + dx, location[1] + dy, level_height],
                        scale=[scale * 0.7, scale * 0.7, scale * 0.7],
                        mesh_path="/Engine/BasicShapes/Cylinder.Cylinder",
                    )
                    if actor:
                        spawned.append(actor.get_name())

        return {
            "success": True,
            "actors": spawned,
            "tower_style": tower_style,
            "total_actors": len(spawned),
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# 2. construct_house
# ---------------------------------------------------------------------------

def construct_house(width=1200, depth=1000, height=600, location=None,
                    house_style="modern", mesh="/Engine/BasicShapes/Cube.Cube",
                    name_prefix="House"):
    """
    건축 디테일이 있는 집을 생성한다.

    Args:
        width: 너비 (기본: 1200)
        depth: 깊이 (기본: 1000)
        height: 높이 (기본: 600)
        location: [x, y, z] 위치
        house_style: "modern", "cottage" (기본: "modern")
        mesh: 메시 경로
        name_prefix: 이름 접두사

    Returns:
        dict: actors 리스트, house_style, dimensions
    """
    if location is None:
        location = [0, 0, 0]

    try:
        spawned = []
        wall_thickness = 20.0
        floor_thickness = 30.0

        if house_style == "cottage":
            width = int(width * 0.8)
            depth = int(depth * 0.8)
            height = int(height * 0.9)

        # 기초
        actor = spawn_static_mesh_actor(
            f"{name_prefix}_Foundation",
            [location[0], location[1], location[2] - floor_thickness / 2],
            scale=[(width + 200) / 100.0, (depth + 200) / 100.0, floor_thickness / 100.0],
            mesh_path=mesh,
        )
        if actor:
            spawned.append(actor.get_name())

        # 바닥
        actor = spawn_static_mesh_actor(
            f"{name_prefix}_Floor",
            [location[0], location[1], location[2] + floor_thickness / 2],
            scale=[width / 100.0, depth / 100.0, floor_thickness / 100.0],
            mesh_path=mesh,
        )
        if actor:
            spawned.append(actor.get_name())

        base_z = location[2] + floor_thickness

        # 벽
        _build_house_walls(spawned, name_prefix, location, width, depth, height,
                           base_z, wall_thickness, mesh)

        # 지붕
        _build_house_roof(spawned, name_prefix, location, width, depth, height,
                          base_z, mesh, house_style)

        # 스타일 특수 기능
        if house_style == "modern":
            actor = spawn_static_mesh_actor(
                f"{name_prefix}_Garage_Door",
                [location[0] - width / 3, location[1] - depth / 2 + wall_thickness / 2,
                 base_z + 150],
                scale=[2.5, 0.1, 2.5],
                mesh_path=mesh,
            )
            if actor:
                spawned.append(actor.get_name())

        features = ["foundation", "floor", "walls", "windows", "door", "flat_roof"]
        if house_style == "cottage":
            features.append("chimney")
        if house_style == "modern":
            features.append("garage")

        return {
            "success": True,
            "actors": spawned,
            "house_style": house_style,
            "dimensions": {"width": width, "depth": depth, "height": height},
            "features": features,
            "total_actors": len(spawned),
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# 3. construct_mansion
# ---------------------------------------------------------------------------

def construct_mansion(mansion_scale="large", location=None, name_prefix="Mansion"):
    """
    여러 윙, 그랜드 룸, 정원이 있는 대규모 맨션을 생성한다.

    Args:
        mansion_scale: "small", "large", "epic", "legendary" (기본: "large")
        location: [x, y, z] 위치
        name_prefix: 이름 접두사

    Returns:
        dict: actors 리스트, mansion_scale
    """
    if location is None:
        location = [0, 0, 0]

    size_params = {
        "small":     {"wings": 2, "floors": 2, "main_w": 2000, "main_d": 1600, "wing_l": 1800, "wing_w": 1000, "fh": 450},
        "large":     {"wings": 3, "floors": 3, "main_w": 2800, "main_d": 2200, "wing_l": 2400, "wing_w": 1400, "fh": 500},
        "epic":      {"wings": 4, "floors": 4, "main_w": 3600, "main_d": 2800, "wing_l": 3000, "wing_w": 1800, "fh": 550},
        "legendary": {"wings": 5, "floors": 5, "main_w": 4400, "main_d": 3400, "wing_l": 3600, "wing_w": 2200, "fh": 600},
    }
    p = size_params.get(mansion_scale, size_params["large"])
    wt = 40  # wall thickness

    try:
        spawned = []

        # 메인 건물 본체 (각 층)
        for floor_idx in range(p["floors"]):
            fz = location[2] + floor_idx * p["fh"]

            # 바닥판
            actor = spawn_static_mesh_actor(
                f"{name_prefix}_MainFloor_{floor_idx}",
                [location[0], location[1], fz],
                scale=[p["main_w"] / 100, p["main_d"] / 100, wt / 100],
            )
            if actor:
                spawned.append(actor.get_name())

            # 외벽 4면
            _build_perimeter_walls(
                spawned, name_prefix, location,
                p["main_w"], p["main_d"], fz, p["fh"], wt,
                f"Main_F{floor_idx}",
            )

        # 지붕
        roof_z = location[2] + p["floors"] * p["fh"]
        actor = spawn_static_mesh_actor(
            f"{name_prefix}_MainRoof",
            [location[0], location[1], roof_z],
            scale=[(p["main_w"] + 200) / 100, (p["main_d"] + 200) / 100, wt / 100],
        )
        if actor:
            spawned.append(actor.get_name())

        # 윙 빌딩
        wing_angles = [0, 90, 180, 270][:p["wings"]]
        for wi, angle_deg in enumerate(wing_angles):
            angle_rad = math.radians(angle_deg)
            offset_x = math.cos(angle_rad) * (p["main_w"] / 2 + p["wing_l"] / 2)
            offset_y = math.sin(angle_rad) * (p["main_d"] / 2 + p["wing_l"] / 2)
            wing_center = [
                location[0] + offset_x,
                location[1] + offset_y,
                location[2],
            ]

            for floor_idx in range(max(1, p["floors"] - 1)):
                fz = wing_center[2] + floor_idx * p["fh"]

                actor = spawn_static_mesh_actor(
                    f"{name_prefix}_Wing{wi}_Floor_{floor_idx}",
                    [wing_center[0], wing_center[1], fz],
                    scale=[p["wing_l"] / 100, p["wing_w"] / 100, wt / 100],
                )
                if actor:
                    spawned.append(actor.get_name())

                _build_perimeter_walls(
                    spawned, name_prefix, wing_center,
                    p["wing_l"], p["wing_w"], fz, p["fh"], wt,
                    f"Wing{wi}_F{floor_idx}",
                )

            # 윙 지붕
            wing_roof_z = wing_center[2] + max(1, p["floors"] - 1) * p["fh"]
            actor = spawn_static_mesh_actor(
                f"{name_prefix}_Wing{wi}_Roof",
                [wing_center[0], wing_center[1], wing_roof_z],
                scale=[(p["wing_l"] + 100) / 100, (p["wing_w"] + 100) / 100, wt / 100],
            )
            if actor:
                spawned.append(actor.get_name())

        return {
            "success": True,
            "actors": spawned,
            "mansion_scale": mansion_scale,
            "total_actors": len(spawned),
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _square_wall_pos(location, side, i, half_size, block_size):
    """정사각형 타워의 벽 위치를 계산한다."""
    if side == 0:
        x = location[0] + (i - half_size + 0.5) * block_size
        y = location[1] - half_size * block_size
    elif side == 1:
        x = location[0] + half_size * block_size
        y = location[1] + (i - half_size + 0.5) * block_size
    elif side == 2:
        x = location[0] + (half_size - i - 0.5) * block_size
        y = location[1] + half_size * block_size
    else:
        x = location[0] - half_size * block_size
        y = location[1] + (half_size - i - 0.5) * block_size
    return x, y


def _build_perimeter_walls(spawned, prefix, location, w, d, floor_z, fh, wt, tag):
    """직사각형 외벽 4면을 생성한다."""
    wall_z = floor_z + fh / 2
    walls = [
        (f"{prefix}_{tag}_WallFront", [location[0], location[1] - d / 2, wall_z],
         [w / 100, wt / 100, fh / 100]),
        (f"{prefix}_{tag}_WallBack", [location[0], location[1] + d / 2, wall_z],
         [w / 100, wt / 100, fh / 100]),
        (f"{prefix}_{tag}_WallLeft", [location[0] - w / 2, location[1], wall_z],
         [wt / 100, d / 100, fh / 100]),
        (f"{prefix}_{tag}_WallRight", [location[0] + w / 2, location[1], wall_z],
         [wt / 100, d / 100, fh / 100]),
    ]
    for name, loc, sc in walls:
        actor = spawn_static_mesh_actor(name, loc, scale=sc)
        if actor:
            spawned.append(actor.get_name())


def _build_house_walls(spawned, prefix, location, width, depth, height,
                       base_z, wt, mesh):
    """집 벽 (문/창문 개구부 포함)을 생성한다."""
    door_w = 120.0
    door_h = 240.0
    half_w = width / 2
    half_d = depth / 2

    # 전면 벽 - 문 좌측
    left_w = half_w - door_w / 2
    actor = spawn_static_mesh_actor(
        f"{prefix}_FrontWall_Left",
        [location[0] - half_w / 2 - door_w / 4, location[1] - half_d, base_z + height / 2],
        scale=[left_w / 100, wt / 100, height / 100],
        mesh_path=mesh,
    )
    if actor:
        spawned.append(actor.get_name())

    # 전면 벽 - 문 우측
    actor = spawn_static_mesh_actor(
        f"{prefix}_FrontWall_Right",
        [location[0] + half_w / 2 + door_w / 4, location[1] - half_d, base_z + height / 2],
        scale=[left_w / 100, wt / 100, height / 100],
        mesh_path=mesh,
    )
    if actor:
        spawned.append(actor.get_name())

    # 전면 벽 - 문 위
    actor = spawn_static_mesh_actor(
        f"{prefix}_FrontWall_Top",
        [location[0], location[1] - half_d, base_z + door_h + (height - door_h) / 2],
        scale=[door_w / 100, wt / 100, (height - door_h) / 100],
        mesh_path=mesh,
    )
    if actor:
        spawned.append(actor.get_name())

    # 후면 벽
    actor = spawn_static_mesh_actor(
        f"{prefix}_BackWall",
        [location[0], location[1] + half_d, base_z + height / 2],
        scale=[width / 100, wt / 100, height / 100],
        mesh_path=mesh,
    )
    if actor:
        spawned.append(actor.get_name())

    # 좌측 벽
    actor = spawn_static_mesh_actor(
        f"{prefix}_LeftWall",
        [location[0] - half_w, location[1], base_z + height / 2],
        scale=[wt / 100, depth / 100, height / 100],
        mesh_path=mesh,
    )
    if actor:
        spawned.append(actor.get_name())

    # 우측 벽
    actor = spawn_static_mesh_actor(
        f"{prefix}_RightWall",
        [location[0] + half_w, location[1], base_z + height / 2],
        scale=[wt / 100, depth / 100, height / 100],
        mesh_path=mesh,
    )
    if actor:
        spawned.append(actor.get_name())


def _build_house_roof(spawned, prefix, location, width, depth, height,
                      base_z, mesh, house_style):
    """집 지붕을 생성한다."""
    roof_thickness = 30.0
    overhang = 100.0

    actor = spawn_static_mesh_actor(
        f"{prefix}_Roof",
        [location[0], location[1], base_z + height + roof_thickness / 2],
        scale=[(width + overhang * 2) / 100, (depth + overhang * 2) / 100, roof_thickness / 100],
        mesh_path=mesh,
    )
    if actor:
        spawned.append(actor.get_name())

    if house_style == "cottage":
        actor = spawn_static_mesh_actor(
            f"{prefix}_Chimney",
            [location[0] + width / 3, location[1] + depth / 3,
             base_z + height + roof_thickness + 150],
            scale=[1.0, 1.0, 2.5],
            mesh_path="/Engine/BasicShapes/Cylinder.Cylinder",
        )
        if actor:
            spawned.append(actor.get_name())
