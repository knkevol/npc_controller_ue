"""
Complex Structures
==================
대형 복합 구조물: 미로, 마을, 성채 요새.
MCP helpers의 maze/town/castle 로직을 UE5 Python API로 포팅.
"""
import math
import random

from skills.structures import spawn_static_mesh_actor


# ---------------------------------------------------------------------------
# Internal spawn wrapper
# ---------------------------------------------------------------------------

def _spawn(name, location, scale=None, mesh="/Engine/BasicShapes/Cube.Cube", rotation=None):
    """spawn_static_mesh_actor 래퍼. 성공 시 이름 반환, 실패 시 None."""
    actor = spawn_static_mesh_actor(
        name=name,
        location=location,
        scale=scale,
        mesh_path=mesh,
        rotation=rotation,
    )
    return name if actor is not None else None


# ===========================================================================
# create_maze
# ===========================================================================

def create_maze(
    rows=8,
    cols=8,
    cell_size=300.0,
    wall_height=3,
    location=None,
):
    """
    재귀 백트래킹 알고리즘으로 풀 수 있는 미로를 생성한다.

    Args:
        rows: 미로 행 수
        cols: 미로 열 수
        cell_size: 셀 크기 (UU)
        wall_height: 벽 높이 (블록 수)
        location: [x, y, z] 중심 위치

    Returns:
        dict: 생성 결과
    """
    if location is None:
        location = [0.0, 0.0, 0.0]

    try:
        spawned = []

        # 미로 그리드 초기화 (True = 벽)
        maze = [[True for _ in range(cols * 2 + 1)] for _ in range(rows * 2 + 1)]

        # 재귀 백트래킹
        def carve_path(row, col):
            maze[row * 2 + 1][col * 2 + 1] = False
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            random.shuffle(directions)
            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                if 0 <= nr < rows and 0 <= nc < cols and maze[nr * 2 + 1][nc * 2 + 1]:
                    maze[row * 2 + 1 + dr][col * 2 + 1 + dc] = False
                    carve_path(nr, nc)

        carve_path(0, 0)

        # 입구/출구
        maze[1][0] = False
        maze[rows * 2 - 1][cols * 2] = False

        maze_h = rows * 2 + 1
        maze_w = cols * 2 + 1
        scale_v = cell_size / 100.0

        for r in range(maze_h):
            for c in range(maze_w):
                if not maze[r][c]:
                    continue
                for h in range(wall_height):
                    x = location[0] + (c - maze_w / 2) * cell_size
                    y = location[1] + (r - maze_h / 2) * cell_size
                    z = location[2] + h * cell_size
                    n = _spawn(
                        f"Maze_Wall_{r}_{c}_{h}",
                        [x, y, z],
                        scale=[scale_v, scale_v, scale_v],
                    )
                    if n:
                        spawned.append(n)

        # 입구/출구 마커
        ent = _spawn(
            "Maze_Entrance",
            [
                location[0] - maze_w / 2 * cell_size - cell_size,
                location[1] + (-maze_h / 2 + 1) * cell_size,
                location[2] + cell_size,
            ],
            scale=[0.5, 0.5, 0.5],
            mesh="/Engine/BasicShapes/Cylinder.Cylinder",
        )
        if ent:
            spawned.append(ent)

        ext = _spawn(
            "Maze_Exit",
            [
                location[0] + maze_w / 2 * cell_size + cell_size,
                location[1] + (-maze_h / 2 + rows * 2 - 1) * cell_size,
                location[2] + cell_size,
            ],
            scale=[0.5, 0.5, 0.5],
            mesh="/Engine/BasicShapes/Sphere.Sphere",
        )
        if ext:
            spawned.append(ext)

        wall_count = sum(1 for n in spawned if "Wall" in n)
        return {
            "success": True,
            "actors": spawned,
            "maze_size": f"{rows}x{cols}",
            "wall_count": wall_count,
            "entrance": "Left side (cylinder marker)",
            "exit": "Right side (sphere marker)",
        }
    except Exception as e:
        return {"error": str(e)}


# ===========================================================================
# create_town
# ===========================================================================

_TOWN_PARAMS = {
    "small": {"blocks": 3, "block_size": 1500, "max_height": 5, "pop": 20, "sky_chance": 0.1},
    "medium": {"blocks": 5, "block_size": 2000, "max_height": 10, "pop": 50, "sky_chance": 0.3},
    "large": {"blocks": 7, "block_size": 2500, "max_height": 20, "pop": 100, "sky_chance": 0.5},
    "metropolis": {"blocks": 10, "block_size": 3000, "max_height": 40, "pop": 200, "sky_chance": 0.7},
}


def create_town(
    town_size="medium",
    building_density=0.7,
    location=None,
    name_prefix="Town",
    include_infrastructure=True,
    architectural_style="mixed",
):
    """
    동적 마을을 생성한다: 건물, 도로, 인프라.

    Args:
        town_size: "small" | "medium" | "large" | "metropolis"
        building_density: 0.0~1.0
        location: [x, y, z]
        name_prefix: 액터 이름 접두사
        include_infrastructure: 인프라(가로등, 차량 등) 포함
        architectural_style: "modern" | "cottage" | "mixed" | "downtown" 등

    Returns:
        dict: 마을 생성 통계
    """
    if location is None:
        location = [0.0, 0.0, 0.0]

    try:
        random.seed()
        tp = _TOWN_PARAMS.get(town_size, _TOWN_PARAMS["medium"])
        blocks = tp["blocks"]
        block_size = tp["block_size"]
        max_height = tp["max_height"]
        target_pop = int(tp["pop"] * building_density)
        sky_chance = tp["sky_chance"]

        all_spawned = []
        street_width = block_size * 0.3

        # 도로 그리드
        street_count = 0
        for i in range(blocks + 1):
            sy = location[1] + (i - blocks / 2) * block_size
            for j in range(blocks):
                sx = location[0] + (j - blocks / 2 + 0.5) * block_size
                n = _spawn(
                    f"{name_prefix}_Street_H_{i}_{j}",
                    [sx, sy, location[2]],
                    scale=[block_size / 100, street_width / 100, 0.1],
                )
                if n:
                    all_spawned.append(n)
                    street_count += 1

        for i in range(blocks + 1):
            sx = location[0] + (i - blocks / 2) * block_size
            for j in range(blocks):
                sy = location[1] + (j - blocks / 2 + 0.5) * block_size
                n = _spawn(
                    f"{name_prefix}_Street_V_{i}_{j}",
                    [sx, sy, location[2]],
                    scale=[street_width / 100, block_size / 100, 0.1],
                )
                if n:
                    all_spawned.append(n)
                    street_count += 1

        # 건물 배치
        building_count = 0
        for bx in range(blocks):
            for by in range(blocks):
                if building_count >= target_pop:
                    break
                if random.random() > building_density:
                    continue

                cx = location[0] + (bx - blocks / 2) * block_size
                cy = location[1] + (by - blocks / 2) * block_size
                is_central = abs(bx - blocks // 2) <= 1 and abs(by - blocks // 2) <= 1

                # 건물 높이 결정
                if is_central and random.random() < sky_chance:
                    h = random.randint(max_height // 2, max_height)
                else:
                    h = random.randint(2, max(3, max_height // 3))

                w = random.uniform(0.6, 1.0) * block_size * 0.3
                d = random.uniform(0.6, 1.0) * block_size * 0.3
                ox = random.uniform(-block_size * 0.15, block_size * 0.15)
                oy = random.uniform(-block_size * 0.15, block_size * 0.15)

                n = _spawn(
                    f"{name_prefix}_Building_{bx}_{by}",
                    [cx + ox, cy + oy, location[2] + h * 50],
                    scale=[w / 100, d / 100, h],
                )
                if n:
                    all_spawned.append(n)
                    building_count += 1

        # 인프라
        infra_count = 0
        if include_infrastructure:
            # 가로등
            for i in range(blocks + 1):
                for j in range(blocks + 1):
                    lx = location[0] + (i - blocks / 2) * block_size
                    ly = location[1] + (j - blocks / 2) * block_size
                    n = _spawn(
                        f"{name_prefix}_Light_{i}_{j}",
                        [lx, ly, location[2] + 250],
                        scale=[0.2, 0.2, 5.0],
                        mesh="/Engine/BasicShapes/Cylinder.Cylinder",
                    )
                    if n:
                        all_spawned.append(n)
                        infra_count += 1

        return {
            "success": True,
            "town_stats": {
                "size": town_size,
                "density": building_density,
                "blocks": blocks,
                "buildings": building_count,
                "infrastructure_items": infra_count,
                "total_actors": len(all_spawned),
                "architectural_style": architectural_style,
            },
            "actors": all_spawned,
        }
    except Exception as e:
        return {"error": str(e)}


# ===========================================================================
# create_castle_fortress
# ===========================================================================

_CASTLE_SIZES = {
    "small": {
        "outer_width": 6000, "outer_depth": 6000,
        "inner_width": 3000, "inner_depth": 3000,
        "wall_height": 800, "tower_count": 8, "tower_height": 1200,
    },
    "medium": {
        "outer_width": 8000, "outer_depth": 8000,
        "inner_width": 4000, "inner_depth": 4000,
        "wall_height": 1000, "tower_count": 12, "tower_height": 1600,
    },
    "large": {
        "outer_width": 12000, "outer_depth": 12000,
        "inner_width": 6000, "inner_depth": 6000,
        "wall_height": 1200, "tower_count": 16, "tower_height": 2000,
    },
    "epic": {
        "outer_width": 16000, "outer_depth": 16000,
        "inner_width": 8000, "inner_depth": 8000,
        "wall_height": 1600, "tower_count": 24, "tower_height": 2800,
    },
}


def _scaled_dims(params, sf=2.0):
    cm = max(1, int(round(sf)))
    return {
        "outer_width": int(params["outer_width"] * sf),
        "outer_depth": int(params["outer_depth"] * sf),
        "inner_width": int(params["inner_width"] * sf),
        "inner_depth": int(params["inner_depth"] * sf),
        "wall_height": int(params["wall_height"] * sf),
        "tower_count": int(params["tower_count"] * cm),
        "tower_height": int(params["tower_height"] * sf),
        "complexity": cm,
        "gate_offset": int(700 * sf),
        "barbican_offset": int(400 * sf),
        "drawbridge_offset": int(600 * sf),
        "wall_thickness": int(300 * max(1.0, sf * 0.75)),
    }


def _corners(loc, w, d):
    return [
        [loc[0] - w / 2, loc[1] - d / 2],
        [loc[0] + w / 2, loc[1] - d / 2],
        [loc[0] + w / 2, loc[1] + d / 2],
        [loc[0] - w / 2, loc[1] + d / 2],
    ]


def create_castle_fortress(
    castle_size="large",
    location=None,
    name_prefix="Castle",
    include_siege_weapons=True,
    include_village=True,
    architectural_style="medieval",
):
    """
    성채 요새를 생성한다: 외벽, 내벽, 타워, 성채, 마을.

    Args:
        castle_size: "small" | "medium" | "large" | "epic"
        location: [x, y, z]
        name_prefix: 액터 이름 접두사
        include_siege_weapons: 공성 무기 포함
        include_village: 주변 마을 포함
        architectural_style: "medieval" | "fantasy" | "gothic"

    Returns:
        dict: 성채 생성 통계
    """
    if location is None:
        location = [0.0, 0.0, 0.0]

    try:
        params = _CASTLE_SIZES.get(castle_size, _CASTLE_SIZES["large"])
        d = _scaled_dims(params)
        actors = []

        # --- 외벽 ---
        _build_walls(name_prefix, location, d, actors)
        # --- 내벽 ---
        _build_inner_walls(name_prefix, location, d, actors)
        # --- 게이트 ---
        _build_gate(name_prefix, location, d, actors)
        # --- 코너 타워 ---
        _build_corner_towers(name_prefix, location, d, architectural_style, actors)
        # --- 내부 코너 타워 ---
        _build_inner_corner_towers(name_prefix, location, d, actors)
        # --- 중간 타워 ---
        _build_intermediate_towers(name_prefix, location, d, actors)
        # --- 중앙 성채 ---
        _build_keep(name_prefix, location, d, actors)
        # --- 안뜰 건물 ---
        _build_courtyard(name_prefix, location, d, actors)
        # --- 공성 무기 ---
        if include_siege_weapons:
            _build_siege(name_prefix, location, d, actors)
        # --- 마을 ---
        if include_village:
            _build_village(name_prefix, location, d, castle_size, actors)
        # --- 도개교/해자 ---
        _build_drawbridge(name_prefix, location, d, actors)
        # --- 깃발 ---
        _build_flags(name_prefix, location, d, actors)

        return {
            "success": True,
            "actors": actors,
            "stats": {
                "size": castle_size,
                "style": architectural_style,
                "towers": d["tower_count"],
                "has_village": include_village,
                "has_siege_weapons": include_siege_weapons,
                "total_actors": len(actors),
            },
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Castle sub-builders
# ---------------------------------------------------------------------------

def _build_walls(pfx, loc, d, actors):
    ow, od, wh, wt = d["outer_width"], d["outer_depth"], d["wall_height"], d["wall_thickness"]
    step = 200
    # North
    for i in range(int(ow / step)):
        x = loc[0] - ow / 2 + i * step + step / 2
        n = _spawn(f"{pfx}_WallN_{i}", [x, loc[1] - od / 2, loc[2] + wh / 2], [2.0, wt / 100, wh / 100])
        if n:
            actors.append(n)
        if i % 2 == 0:
            n = _spawn(f"{pfx}_BattN_{i}", [x, loc[1] - od / 2, loc[2] + wh + 50], [1.0, wt / 100, 1.0])
            if n:
                actors.append(n)
    # South
    for i in range(int(ow / step)):
        x = loc[0] - ow / 2 + i * step + step / 2
        n = _spawn(f"{pfx}_WallS_{i}", [x, loc[1] + od / 2, loc[2] + wh / 2], [2.0, wt / 100, wh / 100])
        if n:
            actors.append(n)
    # East
    for i in range(int(od / step)):
        y = loc[1] - od / 2 + i * step + step / 2
        n = _spawn(f"{pfx}_WallE_{i}", [loc[0] + ow / 2, y, loc[2] + wh / 2], [wt / 100, 2.0, wh / 100])
        if n:
            actors.append(n)
    # West (gate gap)
    for i in range(int(od / step)):
        y = loc[1] - od / 2 + i * step + step / 2
        if abs(y - loc[1]) > 700:
            n = _spawn(f"{pfx}_WallW_{i}", [loc[0] - ow / 2, y, loc[2] + wh / 2], [wt / 100, 2.0, wh / 100])
            if n:
                actors.append(n)


def _build_inner_walls(pfx, loc, d, actors):
    iw, idp, wt = d["inner_width"], d["inner_depth"], d["wall_thickness"]
    iwh = d["wall_height"] * 1.3
    step = 200
    for i in range(int(iw / step)):
        x = loc[0] - iw / 2 + i * step + step / 2
        n = _spawn(f"{pfx}_IWN_{i}", [x, loc[1] - idp / 2, loc[2] + iwh / 2], [2.0, wt / 100, iwh / 100])
        if n:
            actors.append(n)
        n = _spawn(f"{pfx}_IWS_{i}", [x, loc[1] + idp / 2, loc[2] + iwh / 2], [2.0, wt / 100, iwh / 100])
        if n:
            actors.append(n)
    for i in range(int(idp / step)):
        y = loc[1] - idp / 2 + i * step + step / 2
        n = _spawn(f"{pfx}_IWE_{i}", [loc[0] + iw / 2, y, loc[2] + iwh / 2], [wt / 100, 2.0, iwh / 100])
        if n:
            actors.append(n)
        n = _spawn(f"{pfx}_IWW_{i}", [loc[0] - iw / 2, y, loc[2] + iwh / 2], [wt / 100, 2.0, iwh / 100])
        if n:
            actors.append(n)


def _build_gate(pfx, loc, d, actors):
    ow, iw = d["outer_width"], d["inner_width"]
    th, wh = d["tower_height"], d["wall_height"]
    go, bo = d["gate_offset"], d["barbican_offset"]
    cyl = "/Engine/BasicShapes/Cylinder.Cylinder"
    cone = "/Engine/BasicShapes/Cone.Cone"
    for side in [-1, 1]:
        _spawn(f"{pfx}_GateTower_{side}", [loc[0] - ow / 2, loc[1] + side * go, loc[2] + th / 2], [4.0, 4.0, th / 100], cyl)
        n = _spawn(f"{pfx}_GateTowerTop_{side}", [loc[0] - ow / 2, loc[1] + side * go, loc[2] + th + 200], [5.0, 5.0, 0.8], cone)
        if n:
            actors.append(n)
    _spawn(f"{pfx}_Barbican", [loc[0] - ow / 2 - bo, loc[1], loc[2] + wh / 2], [8.0, 12.0, wh / 100])
    n = _spawn(f"{pfx}_Portcullis", [loc[0] - ow / 2, loc[1], loc[2] + 200], [0.5, 12.0, 8.0])
    if n:
        actors.append(n)
    n = _spawn(f"{pfx}_InnerPort", [loc[0] - iw / 2, loc[1], loc[2] + 200], [0.5, 8.0, 6.0])
    if n:
        actors.append(n)


def _build_corner_towers(pfx, loc, d, style, actors):
    ow, od, th = d["outer_width"], d["outer_depth"], d["tower_height"]
    cyl = "/Engine/BasicShapes/Cylinder.Cylinder"
    cone = "/Engine/BasicShapes/Cone.Cone"
    for i, c in enumerate(_corners(loc, ow, od)):
        _spawn(f"{pfx}_TBase_{i}", [c[0], c[1], loc[2] + 150], [6.0, 6.0, 3.0], cyl)
        n = _spawn(f"{pfx}_Tower_{i}", [c[0], c[1], loc[2] + th / 2], [5.0, 5.0, th / 100], cyl)
        if n:
            actors.append(n)
        if style in ("medieval", "fantasy"):
            n = _spawn(f"{pfx}_TTop_{i}", [c[0], c[1], loc[2] + th + 150], [6.0, 6.0, 2.5], cone)
            if n:
                actors.append(n)


def _build_inner_corner_towers(pfx, loc, d, actors):
    iw, idp, th = d["inner_width"], d["inner_depth"], d["tower_height"]
    cyl = "/Engine/BasicShapes/Cylinder.Cylinder"
    cone = "/Engine/BasicShapes/Cone.Cone"
    ith = th * 1.4
    for i, c in enumerate(_corners(loc, iw, idp)):
        _spawn(f"{pfx}_ITBase_{i}", [c[0], c[1], loc[2] + 200], [8.0, 8.0, 4.0], cyl)
        n = _spawn(f"{pfx}_ITower_{i}", [c[0], c[1], loc[2] + ith / 2], [6.0, 6.0, ith / 100], cyl)
        if n:
            actors.append(n)
        n = _spawn(f"{pfx}_ITTop_{i}", [c[0], c[1], loc[2] + ith + 200], [8.0, 8.0, 3.0], cone)
        if n:
            actors.append(n)


def _build_intermediate_towers(pfx, loc, d, actors):
    ow, od, th = d["outer_width"], d["outer_depth"], d["tower_height"]
    cm = d["complexity"]
    cyl = "/Engine/BasicShapes/Cylinder.Cylinder"
    count = max(3, 3 * cm)
    for i in range(count):
        tx = loc[0] - ow / 4 + i * ow / 4
        n = _spawn(f"{pfx}_NWT_{i}", [tx, loc[1] - od / 2, loc[2] + th * 0.4], [3.0, 3.0, th * 0.8 / 100], cyl)
        if n:
            actors.append(n)
        n = _spawn(f"{pfx}_SWT_{i}", [tx, loc[1] + od / 2, loc[2] + th * 0.4], [3.0, 3.0, th * 0.8 / 100], cyl)
        if n:
            actors.append(n)


def _build_keep(pfx, loc, d, actors):
    iw, idp, th = d["inner_width"], d["inner_depth"], d["tower_height"]
    kw, kd = iw * 0.6, idp * 0.6
    kh = th * 2.0
    cyl = "/Engine/BasicShapes/Cylinder.Cylinder"
    n = _spawn(f"{pfx}_KeepBase", [loc[0], loc[1], loc[2] + kh / 2], [kw / 100, kd / 100, kh / 100])
    if n:
        actors.append(n)
    spire_h = max(1200.0, th)
    n = _spawn(f"{pfx}_KeepTower", [loc[0], loc[1], loc[2] + kh + spire_h / 2], [4.0, 4.0, spire_h / 100], cyl)
    if n:
        actors.append(n)
    n = _spawn(f"{pfx}_GreatHall", [loc[0], loc[1] + kd / 3, loc[2] + 200], [kw / 100 * 0.8, kd / 100 * 0.5, 6.0])
    if n:
        actors.append(n)
    # Keep corner towers
    for i, c in enumerate([
        [loc[0] - kw / 3, loc[1] - kd / 3],
        [loc[0] + kw / 3, loc[1] - kd / 3],
        [loc[0] + kw / 3, loc[1] + kd / 3],
        [loc[0] - kw / 3, loc[1] + kd / 3],
    ]):
        n = _spawn(f"{pfx}_KCT_{i}", [c[0], c[1], loc[2] + kh * 0.8], [3.0, 3.0, kh / 100 * 0.8], cyl)
        if n:
            actors.append(n)


def _build_courtyard(pfx, loc, d, actors):
    iw, idp = d["inner_width"], d["inner_depth"]
    cyl = "/Engine/BasicShapes/Cylinder.Cylinder"
    buildings = [
        ("Stables", [-iw / 3, idp / 3, 150], [8.0, 4.0, 3.0], None),
        ("Barracks", [iw / 3, idp / 3, 150], [10.0, 6.0, 3.0], None),
        ("Blacksmith", [iw / 3, -idp / 3, 100], [6.0, 6.0, 2.0], None),
        ("Well", [-iw / 4, 0, 50], [3.0, 3.0, 2.0], cyl),
        ("Armory", [-iw / 3, -idp / 3, 150], [6.0, 4.0, 3.0], None),
        ("Chapel", [0, -idp / 3, 200], [8.0, 5.0, 4.0], None),
    ]
    for bname, off, sc, mesh in buildings:
        m = mesh or "/Engine/BasicShapes/Cube.Cube"
        n = _spawn(f"{pfx}_{bname}", [loc[0] + off[0], loc[1] + off[1], loc[2] + off[2]], sc, m)
        if n:
            actors.append(n)


def _build_siege(pfx, loc, d, actors):
    ow, od, wh, th = d["outer_width"], d["outer_depth"], d["wall_height"], d["tower_height"]
    positions = [
        [loc[0], loc[1] - od / 2 + 200, loc[2] + wh],
        [loc[0], loc[1] + od / 2 - 200, loc[2] + wh],
        [loc[0] - ow / 3, loc[1] - od / 2 + 200, loc[2] + wh],
        [loc[0] + ow / 3, loc[1] + od / 2 - 200, loc[2] + wh],
    ]
    for i, pos in enumerate(positions):
        _spawn(f"{pfx}_CatBase_{i}", pos, [4.0, 3.0, 1.0])
        n = _spawn(f"{pfx}_CatArm_{i}", [pos[0], pos[1], pos[2] + 100], [0.4, 0.4, 6.0], rotation=[45, 0, 0])
        if n:
            actors.append(n)
        for j in range(3):
            n = _spawn(
                f"{pfx}_Ammo_{i}_{j}",
                [pos[0] + j * 80 - 80, pos[1] + 250, pos[2] + 40],
                [0.6, 0.6, 0.6],
                "/Engine/BasicShapes/Sphere.Sphere",
            )
            if n:
                actors.append(n)
    # Ballista on corner towers
    for i, c in enumerate(_corners(loc, ow, od)):
        n = _spawn(f"{pfx}_Ballista_{i}", [c[0], c[1], loc[2] + th], [0.5, 3.0, 0.5])
        if n:
            actors.append(n)


def _build_village(pfx, loc, d, castle_size, actors):
    ow, od = d["outer_width"], d["outer_depth"]
    cm = d["complexity"]
    village_r = ow * 0.3
    num = (24 if castle_size == "epic" else 16) * cm
    cone = "/Engine/BasicShapes/Cone.Cone"
    for i in range(num):
        angle = 2 * math.pi * i / num
        hx = loc[0] + (ow / 2 + village_r) * math.cos(angle)
        hy = loc[1] + (od / 2 + village_r) * math.sin(angle)
        if hx < loc[0] - ow * 0.4 and abs(hy - loc[1]) < 1000:
            continue
        deg = angle * 180 / math.pi
        n = _spawn(f"{pfx}_VHouse_{i}", [hx, hy, loc[2] + 100], [3.0, 2.5, 2.0], rotation=[0, deg, 0])
        if n:
            actors.append(n)
        n = _spawn(f"{pfx}_VRoof_{i}", [hx, hy, loc[2] + 250], [3.5, 3.0, 0.8], cone, rotation=[0, deg, 0])
        if n:
            actors.append(n)
    # Market stalls
    sf = 2.0
    mx_start = loc[0] - ow / 2 - int(800 * sf)
    for i in range(8 * cm):
        sx = mx_start + i * 150
        sy = loc[1] + (200 if i % 2 == 0 else -200)
        n = _spawn(f"{pfx}_Stall_{i}", [sx, sy, loc[2] + 80], [2.0, 1.5, 1.5])
        if n:
            actors.append(n)


def _build_drawbridge(pfx, loc, d, actors):
    ow, od = d["outer_width"], d["outer_depth"]
    dbo = d["drawbridge_offset"]
    sf = 2.0
    n = _spawn(f"{pfx}_Drawbridge", [loc[0] - ow / 2 - dbo, loc[1], loc[2] + 20], [12.0 * sf, 10.0 * sf, 0.3])
    if n:
        actors.append(n)
    # Moat
    cm = d["complexity"]
    moat_w = int(1200 * sf)
    sections = int(30 * cm)
    cyl = "/Engine/BasicShapes/Cylinder.Cylinder"
    for i in range(sections):
        angle = 2 * math.pi * i / sections
        mx = loc[0] + (ow / 2 + moat_w / 2) * math.cos(angle)
        my = loc[1] + (od / 2 + moat_w / 2) * math.sin(angle)
        n = _spawn(f"{pfx}_Moat_{i}", [mx, my, loc[2] - 50], [moat_w / 100, moat_w / 100, 0.1], cyl)
        if n:
            actors.append(n)


def _build_flags(pfx, loc, d, actors):
    ow, od, th = d["outer_width"], d["outer_depth"], d["tower_height"]
    go = d["gate_offset"]
    cyl = "/Engine/BasicShapes/Cylinder.Cylinder"
    positions = []
    for c in _corners(loc, ow, od):
        positions.append([c[0], c[1], loc[2] + th + 300])
    for side in [1, -1]:
        positions.append([loc[0] - ow / 2, loc[1] + side * go, loc[2] + th + 200])
    for i, fp in enumerate(positions):
        _spawn(f"{pfx}_Pole_{i}", fp, [0.05, 0.05, 3.0], cyl)
        n = _spawn(f"{pfx}_Flag_{i}", [fp[0] + 100, fp[1], fp[2] + 100], [0.05, 2.0, 1.5])
        if n:
            actors.append(n)
