"""
Primitive Structures
====================
피라미드, 벽, 타워, 계단, 아치 등 기본 구조물 생성.
MCP의 create_pyramid / create_wall / create_tower / create_staircase / create_arch에 대응.
"""

import math
from skills.structures import spawn_static_mesh_actor


def create_pyramid(
    base_size=3,
    block_size=100.0,
    location=None,
    name_prefix="PyramidBlock",
    mesh="/Engine/BasicShapes/Cube.Cube",
):
    """큐브로 피라미드를 생성한다.

    Args:
        base_size (int): 밑변 블록 수.
        block_size (float): 블록 한 변 크기(cm).
        location (list[float]): [x, y, z] 중심 위치.
        name_prefix (str): 액터 이름 접두사.
        mesh (str): 메시 에셋 경로.

    Returns:
        dict: {"spawned": [...], "count": int}
    """
    if location is None:
        location = [0.0, 0.0, 0.0]

    try:
        spawned = []
        scale = block_size / 100.0

        for level in range(base_size):
            count = base_size - level
            for x in range(count):
                for y in range(count):
                    name = f"{name_prefix}_{level}_{x}_{y}"
                    loc = [
                        location[0] + (x - (count - 1) / 2) * block_size,
                        location[1] + (y - (count - 1) / 2) * block_size,
                        location[2] + level * block_size,
                    ]
                    actor = spawn_static_mesh_actor(
                        name=name,
                        location=loc,
                        scale=[scale, scale, scale],
                        mesh_path=mesh,
                    )
                    if actor is not None:
                        spawned.append(actor.get_name())

        return {"spawned": spawned, "count": len(spawned)}
    except Exception as e:
        return {"error": str(e)}


def create_wall(
    length=5,
    height=2,
    block_size=100.0,
    location=None,
    orientation="x",
    name_prefix="WallBlock",
    mesh="/Engine/BasicShapes/Cube.Cube",
):
    """큐브로 벽을 생성한다.

    Args:
        length (int): 가로 블록 수.
        height (int): 세로 블록 수.
        block_size (float): 블록 크기(cm).
        location (list[float]): 시작 위치.
        orientation (str): "x" 또는 "y" 방향.
        name_prefix (str): 액터 이름 접두사.
        mesh (str): 메시 에셋 경로.

    Returns:
        dict: {"spawned": [...], "count": int}
    """
    if location is None:
        location = [0.0, 0.0, 0.0]

    try:
        spawned = []
        scale = block_size / 100.0

        for h in range(height):
            for i in range(length):
                name = f"{name_prefix}_{h}_{i}"
                if orientation == "x":
                    loc = [
                        location[0] + i * block_size,
                        location[1],
                        location[2] + h * block_size,
                    ]
                else:
                    loc = [
                        location[0],
                        location[1] + i * block_size,
                        location[2] + h * block_size,
                    ]
                actor = spawn_static_mesh_actor(
                    name=name,
                    location=loc,
                    scale=[scale, scale, scale],
                    mesh_path=mesh,
                )
                if actor is not None:
                    spawned.append(actor.get_name())

        return {"spawned": spawned, "count": len(spawned)}
    except Exception as e:
        return {"error": str(e)}


def create_tower(
    height=10,
    base_size=4,
    block_size=100.0,
    location=None,
    name_prefix="TowerBlock",
    mesh="/Engine/BasicShapes/Cube.Cube",
    tower_style="cylindrical",
):
    """타워를 생성한다. cylindrical / square / tapered 스타일 지원.

    Args:
        height (int): 층 수.
        base_size (int): 밑면 크기(블록 수 또는 지름 기준).
        block_size (float): 블록 크기(cm).
        location (list[float]): 중심 위치.
        name_prefix (str): 액터 이름 접두사.
        mesh (str): 메시 에셋 경로.
        tower_style (str): "cylindrical", "square", "tapered".

    Returns:
        dict: {"spawned": [...], "count": int, "tower_style": str}
    """
    if location is None:
        location = [0.0, 0.0, 0.0]

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
                    name = f"{name_prefix}_{level}_{i}"
                    actor = spawn_static_mesh_actor(
                        name=name,
                        location=[x, y, level_height],
                        scale=[scale, scale, scale],
                        mesh_path=mesh,
                    )
                    if actor is not None:
                        spawned.append(actor.get_name())

            elif tower_style == "tapered":
                current_size = max(1, base_size - (level // 2))
                half_size = current_size / 2
                _build_square_ring(
                    spawned, name_prefix, level, current_size, half_size,
                    block_size, scale, location, level_height, mesh,
                )

            else:  # square
                half_size = base_size / 2
                _build_square_ring(
                    spawned, name_prefix, level, base_size, half_size,
                    block_size, scale, location, level_height, mesh,
                )

            # 장식 요소 (3층마다)
            if level % 3 == 2 and level < height - 1:
                for corner in range(4):
                    angle = corner * math.pi / 2
                    dx = (base_size / 2 + 0.5) * block_size * math.cos(angle)
                    dy = (base_size / 2 + 0.5) * block_size * math.sin(angle)
                    name = f"{name_prefix}_{level}_detail_{corner}"
                    actor = spawn_static_mesh_actor(
                        name=name,
                        location=[location[0] + dx, location[1] + dy, level_height],
                        scale=[scale * 0.7, scale * 0.7, scale * 0.7],
                        mesh_path="/Engine/BasicShapes/Cylinder.Cylinder",
                    )
                    if actor is not None:
                        spawned.append(actor.get_name())

        return {"spawned": spawned, "count": len(spawned), "tower_style": tower_style}
    except Exception as e:
        return {"error": str(e)}


def _build_square_ring(
    spawned, prefix, level, size, half_size, block_size, scale,
    location, level_height, mesh,
):
    """정사각형 타워 한 층의 네 벽면을 생성한다. (내부 헬퍼)"""
    side_names = ["front", "right", "back", "left"]
    for side in range(4):
        for i in range(size):
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

            name = f"{prefix}_{level}_{side_names[side]}_{i}"
            actor = spawn_static_mesh_actor(
                name=name,
                location=[x, y, level_height],
                scale=[scale, scale, scale],
                mesh_path=mesh,
            )
            if actor is not None:
                spawned.append(actor.get_name())


def create_staircase(
    steps=5,
    step_size=None,
    location=None,
    name_prefix="Stair",
    mesh="/Engine/BasicShapes/Cube.Cube",
):
    """큐브로 계단을 생성한다.

    Args:
        steps (int): 계단 수.
        step_size (list[float]): [width, depth, height] 각 스텝 크기(cm). 기본 [100, 100, 50].
        location (list[float]): 시작 위치.
        name_prefix (str): 액터 이름 접두사.
        mesh (str): 메시 에셋 경로.

    Returns:
        dict: {"spawned": [...], "count": int}
    """
    if step_size is None:
        step_size = [100.0, 100.0, 50.0]
    if location is None:
        location = [0.0, 0.0, 0.0]

    try:
        spawned = []
        sx, sy, sz = step_size

        for i in range(steps):
            name = f"{name_prefix}_{i}"
            loc = [
                location[0] + i * sx,
                location[1],
                location[2] + i * sz,
            ]
            scale = [sx / 100.0, sy / 100.0, sz / 100.0]
            actor = spawn_static_mesh_actor(
                name=name,
                location=loc,
                scale=scale,
                mesh_path=mesh,
            )
            if actor is not None:
                spawned.append(actor.get_name())

        return {"spawned": spawned, "count": len(spawned)}
    except Exception as e:
        return {"error": str(e)}


def create_arch(
    radius=300.0,
    segments=6,
    location=None,
    name_prefix="ArchBlock",
    mesh="/Engine/BasicShapes/Cube.Cube",
):
    """큐브로 반원형 아치를 생성한다.

    Args:
        radius (float): 아치 반지름(cm).
        segments (int): 세그먼트 수.
        location (list[float]): 중심 위치.
        name_prefix (str): 액터 이름 접두사.
        mesh (str): 메시 에셋 경로.

    Returns:
        dict: {"spawned": [...], "count": int}
    """
    if location is None:
        location = [0.0, 0.0, 0.0]

    try:
        spawned = []
        angle_step = math.pi / segments
        scale = radius / 300.0 / 2

        for i in range(segments + 1):
            theta = angle_step * i
            x = radius * math.cos(theta)
            z = radius * math.sin(theta)
            name = f"{name_prefix}_{i}"
            actor = spawn_static_mesh_actor(
                name=name,
                location=[location[0] + x, location[1], location[2] + z],
                scale=[scale, scale, scale],
                mesh_path=mesh,
            )
            if actor is not None:
                spawned.append(actor.get_name())

        return {"spawned": spawned, "count": len(spawned)}
    except Exception as e:
        return {"error": str(e)}
