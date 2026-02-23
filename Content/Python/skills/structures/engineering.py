"""
Engineering Structures
======================
현수교, 수도교 등 대형 엔지니어링 구조물 생성.
MCP의 create_suspension_bridge / create_aqueduct에 대응.
"""

import math
from skills.structures import spawn_static_mesh_actor


# ---------------------------------------------------------------------------
# Suspension Bridge
# ---------------------------------------------------------------------------

def _calculate_parabolic_cable_points(span_length, sag_ratio, tower_height, module_size, start_location):
    """포물선 케이블 좌표를 계산한다. (location, angle) 튜플 리스트 반환."""
    points = []
    sag = span_length * sag_ratio
    a = 4 * sag / (span_length ** 2)
    num_segments = max(1, int(span_length / module_size))

    for i in range(num_segments + 1):
        x = -span_length / 2 + (i * span_length / num_segments)
        y_relative = a * x * x - sag

        world_x = start_location[0] + x
        world_y = start_location[1]
        world_z = start_location[2] + tower_height + y_relative

        if i < num_segments:
            next_x = -span_length / 2 + ((i + 1) * span_length / num_segments)
            next_y_rel = a * next_x * next_x - sag
            angle = math.degrees(math.atan2(next_y_rel - y_relative, next_x - x))
        else:
            angle = 0

        points.append(([world_x, world_y, world_z], angle))
    return points


def create_suspension_bridge(
    span_length=6000,
    deck_width=800,
    tower_height=4000,
    cable_sag_ratio=0.12,
    module_size=200,
    location=None,
    orientation="x",
    name_prefix="Bridge",
    deck_mesh="/Engine/BasicShapes/Cube.Cube",
    tower_mesh="/Engine/BasicShapes/Cube.Cube",
    cable_mesh="/Engine/BasicShapes/Cylinder.Cylinder",
    suspender_mesh="/Engine/BasicShapes/Cylinder.Cylinder",
):
    """현수교를 생성한다.

    Args:
        span_length (float): 타워 간 스팬 길이.
        deck_width (float): 데크 폭.
        tower_height (float): 타워 높이.
        cable_sag_ratio (float): 케이블 처짐 비율 (0.1-0.15).
        module_size (float): 세그먼트 해상도.
        location (list[float]): 중심 위치.
        orientation (str): "x" 또는 "y".
        name_prefix (str): 액터 접두사.
        deck_mesh (str): 데크 메시.
        tower_mesh (str): 타워 메시.
        cable_mesh (str): 케이블 메시.
        suspender_mesh (str): 수직 서스펜더 메시.

    Returns:
        dict: {"spawned": [...], "counts": {...}}
    """
    if location is None:
        location = [0.0, 0.0, 0.0]

    try:
        spawned = []
        counts = {"towers": 0, "deck_segments": 0, "cable_segments": 0, "suspenders": 0}

        loc = location[:]
        span_dir = 1 if orientation == "y" else 0
        cable_offsets = [-deck_width / 2, deck_width / 2]

        # --- Towers ---
        tower_positions = [-span_length / 2, span_length / 2]
        for i, tp in enumerate(tower_positions):
            tl = loc[:]
            tl[span_dir] += tp

            # Base
            a = spawn_static_mesh_actor(
                f"{name_prefix}_Tower_{i}_Base",
                [tl[0], tl[1], tl[2] + 200],
                scale=[5.0, 5.0, 4.0], mesh_path=tower_mesh,
            )
            if a: spawned.append(a.get_name()); counts["towers"] += 1

            # Main shaft
            a = spawn_static_mesh_actor(
                f"{name_prefix}_Tower_{i}_Main",
                [tl[0], tl[1], tl[2] + 400 + tower_height / 2],
                scale=[3.0, 3.0, tower_height / 100], mesh_path=tower_mesh,
            )
            if a: spawned.append(a.get_name()); counts["towers"] += 1

            # Top cap
            top_z = tl[2] + 400 + tower_height
            a = spawn_static_mesh_actor(
                f"{name_prefix}_Tower_{i}_Top",
                [tl[0], tl[1], top_z],
                scale=[3.5, 3.5, 1.0], mesh_path=tower_mesh,
            )
            if a: spawned.append(a.get_name()); counts["towers"] += 1

            # Cable attachments
            for co in cable_offsets:
                al = [tl[0], tl[1], top_z]
                al[1 if span_dir == 0 else 0] += co
                a = spawn_static_mesh_actor(
                    f"{name_prefix}_Tower_{i}_Att_{int(co)}",
                    al, scale=[0.5, 0.5, 0.5], mesh_path=tower_mesh,
                )
                if a: spawned.append(a.get_name()); counts["towers"] += 1

        # --- Cables ---
        effective_h = 400 + tower_height
        cable_points = _calculate_parabolic_cable_points(
            span_length, cable_sag_ratio, effective_h, module_size, loc,
        )

        for ci, offset in enumerate(cable_offsets):
            for i in range(len(cable_points) - 1):
                pt, angle = cable_points[i]
                npt, _ = cable_points[i + 1]

                if span_dir == 0:
                    cl = [(pt[0] + npt[0]) / 2, pt[1] + offset, (pt[2] + npt[2]) / 2]
                    rot = [angle, 0, 0]
                    dx = npt[0] - pt[0]
                else:
                    cl = [loc[0] + offset, (pt[0] + npt[0]) / 2, (pt[2] + npt[2]) / 2]
                    rot = [0, angle, 0]
                    dx = 0

                dz = npt[2] - pt[2]
                seg_len = math.sqrt(dx * dx + dz * dz)

                a = spawn_static_mesh_actor(
                    f"{name_prefix}_Cable_{ci}_{i}",
                    cl, scale=[0.3, 0.3, seg_len / 100],
                    mesh_path=cable_mesh, rotation=rot,
                )
                if a: spawned.append(a.get_name()); counts["cable_segments"] += 1

        # --- Deck ---
        dseg_x = max(1, int(span_length / module_size))
        dseg_y = max(1, int(deck_width / module_size))

        for i in range(dseg_x):
            for j in range(dseg_y):
                if span_dir == 0:
                    dx = loc[0] - span_length / 2 + (i + 0.5) * module_size
                    dy = loc[1] - deck_width / 2 + (j + 0.5) * module_size
                else:
                    dx = loc[0] - deck_width / 2 + (j + 0.5) * module_size
                    dy = loc[1] - span_length / 2 + (i + 0.5) * module_size

                a = spawn_static_mesh_actor(
                    f"{name_prefix}_Deck_{i}_{j}",
                    [dx, dy, loc[2]],
                    scale=[module_size / 100, module_size / 100, 0.5],
                    mesh_path=deck_mesh,
                )
                if a: spawned.append(a.get_name()); counts["deck_segments"] += 1

        # --- Suspenders ---
        susp_spacing = module_size * 3
        num_susp = max(1, int(span_length / susp_spacing))

        for i in range(num_susp):
            x_pos = -span_length / 2 + (i + 0.5) * susp_spacing
            cable_h_rel = cable_sag_ratio * span_length * (
                4 * x_pos * x_pos / (span_length ** 2) - 1
            )
            cable_z = loc[2] + effective_h + cable_h_rel
            susp_h = cable_z - loc[2]

            for offset in cable_offsets:
                if span_dir == 0:
                    sl = [loc[0] + x_pos, loc[1] + offset, (cable_z + loc[2]) / 2]
                else:
                    sl = [loc[0] + offset, loc[1] + x_pos, (cable_z + loc[2]) / 2]

                a = spawn_static_mesh_actor(
                    f"{name_prefix}_Susp_{i}_{int(offset)}",
                    sl, scale=[0.1, 0.1, susp_h / 100],
                    mesh_path=suspender_mesh,
                )
                if a: spawned.append(a.get_name()); counts["suspenders"] += 1

        return {"spawned": spawned, "count": len(spawned), "counts": counts}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Aqueduct
# ---------------------------------------------------------------------------

def _calculate_arch_points(arch_radius, module_size, pier_width, arch_index, tier_height, location, orientation):
    """반원형 아치 좌표를 계산한다."""
    points = []
    circumference = math.pi * arch_radius
    num_segments = max(4, int(circumference / module_size))
    arch_span_x = arch_index * (2 * arch_radius + pier_width) + pier_width / 2

    for i in range(num_segments + 1):
        angle = i * math.pi / num_segments
        x_rel = arch_radius * math.cos(angle)
        z_rel = arch_radius * math.sin(angle)

        if orientation == "x":
            wx = location[0] + arch_span_x + arch_radius + x_rel
            wy = location[1]
        else:
            wx = location[0]
            wy = location[1] + arch_span_x + arch_radius + x_rel

        wz = location[2] + tier_height + z_rel

        if i < num_segments:
            na = (i + 1) * math.pi / num_segments
            dx = math.cos(na) - math.cos(angle)
            dz = math.sin(na) - math.sin(angle)
            tangent = math.degrees(math.atan2(dz, dx))
        else:
            tangent = 90

        points.append(([wx, wy, wz], tangent))
    return points


def create_aqueduct(
    arches=18,
    arch_radius=600,
    pier_width=200,
    tiers=2,
    deck_width=600,
    module_size=200,
    location=None,
    orientation="x",
    name_prefix="Aqueduct",
    arch_mesh="/Engine/BasicShapes/Cylinder.Cylinder",
    pier_mesh="/Engine/BasicShapes/Cube.Cube",
    deck_mesh="/Engine/BasicShapes/Cube.Cube",
):
    """다층 로마식 수도교를 생성한다.

    Args:
        arches (int): 티어별 아치 수.
        arch_radius (float): 아치 반지름.
        pier_width (float): 기둥 폭.
        tiers (int): 층 수 (1-3 권장).
        deck_width (float): 수로 폭.
        module_size (float): 세그먼트 해상도.
        location (list[float]): 시작 위치.
        orientation (str): "x" 또는 "y".
        name_prefix (str): 액터 접두사.
        arch_mesh (str): 아치 메시.
        pier_mesh (str): 기둥 메시.
        deck_mesh (str): 데크 메시.

    Returns:
        dict: {"spawned": [...], "counts": {...}}
    """
    if location is None:
        location = [0.0, 0.0, 0.0]

    try:
        spawned = []
        counts = {"arch_segments": 0, "piers": 0, "deck_segments": 0}

        arch_spacing = 2 * arch_radius + pier_width
        total_length = arches * arch_spacing + pier_width
        tier_height = 2 * arch_radius + pier_width

        for tier in range(tiers):
            cur_h = tier * tier_height
            pier_scale_factor = 1.0 - (tier * 0.1)

            # Piers
            for pi in range(arches + 1):
                px = pi * arch_spacing
                if orientation == "x":
                    pl = [location[0] + px, location[1], location[2] + cur_h]
                else:
                    pl = [location[0], location[1] + px, location[2] + cur_h]

                a = spawn_static_mesh_actor(
                    f"{name_prefix}_Pier_T{tier}_P{pi}",
                    pl,
                    scale=[
                        pier_width / 100 * pier_scale_factor,
                        pier_width / 100 * pier_scale_factor,
                        tier_height / 100,
                    ],
                    mesh_path=pier_mesh,
                )
                if a: spawned.append(a.get_name()); counts["piers"] += 1

            # Arches
            for ai in range(arches):
                arch_pts = _calculate_arch_points(
                    arch_radius, module_size, pier_width, ai, cur_h, location, orientation,
                )
                for si in range(len(arch_pts) - 1):
                    pt, angle = arch_pts[si]
                    npt, _ = arch_pts[si + 1]
                    mx = (pt[0] + npt[0]) / 2
                    my = (pt[1] + npt[1]) / 2
                    mz = (pt[2] + npt[2]) / 2
                    dx = npt[0] - pt[0]
                    dy = npt[1] - pt[1]
                    dz = npt[2] - pt[2]
                    seg_len = math.sqrt(dx * dx + dy * dy + dz * dz)

                    if orientation == "x":
                        rot = [angle, 0, 90]
                    else:
                        rot = [0, angle, 90]

                    a = spawn_static_mesh_actor(
                        f"{name_prefix}_Arch_T{tier}_A{ai}_S{si}",
                        [mx, my, mz],
                        scale=[
                            pier_width / 200 * pier_scale_factor,
                            pier_width / 200 * pier_scale_factor,
                            seg_len / 100,
                        ],
                        mesh_path=arch_mesh,
                        rotation=rot,
                    )
                    if a: spawned.append(a.get_name()); counts["arch_segments"] += 1

        # Deck
        deck_h = location[2] + tiers * tier_height
        dseg_l = max(1, int(total_length / module_size))
        dseg_w = max(1, int(deck_width / module_size))

        for i in range(dseg_l):
            for j in range(dseg_w):
                if orientation == "x":
                    dx = location[0] + (i + 0.5) * module_size
                    dy = location[1] - deck_width / 2 + (j + 0.5) * module_size
                else:
                    dx = location[0] - deck_width / 2 + (j + 0.5) * module_size
                    dy = location[1] + (i + 0.5) * module_size

                a = spawn_static_mesh_actor(
                    f"{name_prefix}_Deck_{i}_{j}",
                    [dx, dy, deck_h],
                    scale=[module_size / 100, module_size / 100, 0.5],
                    mesh_path=deck_mesh,
                )
                if a: spawned.append(a.get_name()); counts["deck_segments"] += 1

        # Side walls
        for side in [0, 1]:
            for i in range(dseg_l):
                if orientation == "x":
                    wx = location[0] + (i + 0.5) * module_size
                    wy = location[1] + (deck_width / 2 if side else -deck_width / 2)
                else:
                    wx = location[0] + (deck_width / 2 if side else -deck_width / 2)
                    wy = location[1] + (i + 0.5) * module_size

                a = spawn_static_mesh_actor(
                    f"{name_prefix}_Wall_S{side}_{i}",
                    [wx, wy, deck_h + 100],
                    scale=[module_size / 100, 0.2, 2.0],
                    mesh_path=deck_mesh,
                )
                if a: spawned.append(a.get_name()); counts["deck_segments"] += 1

        return {"spawned": spawned, "count": len(spawned), "counts": counts}
    except Exception as e:
        return {"error": str(e)}
