"""
Editor Operations - PIE / Screenshot skills
=============================================
PIE(Play In Editor) 모드 제어 및 스크린샷 촬영 기능.
"""

import unreal


def start_pie():
    """PIE(Play In Editor) 모드를 시작한다."""
    try:
        subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        subsystem.editor_request_begin_play()
        return {"success": True, "message": "PIE started"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def stop_pie():
    """PIE 모드를 종료한다."""
    try:
        subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        subsystem.editor_request_end_play()
        return {"success": True, "message": "PIE stopped"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def is_pie_active():
    """현재 PIE 모드 실행 중인지 확인한다."""
    try:
        subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        active = subsystem.is_in_play_in_editor()
        return {"active": active}
    except Exception as e:
        return {"success": False, "error": str(e)}


def simulate_pie():
    """Simulate 모드를 시작한다 (PIE와 다름)."""
    try:
        subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        subsystem.editor_play_simulate()
        return {"success": True, "message": "Simulate mode started"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def take_screenshot(filename="screenshot.png", res_x=1920, res_y=1080):
    """현재 뷰포트의 고해상도 스크린샷을 촬영한다.

    Args:
        filename: 저장할 파일 경로 (절대 경로 또는 프로젝트 상대 경로)
        res_x: 가로 해상도
        res_y: 세로 해상도
    """
    try:
        if not ('/' in filename or '\\' in filename):
            screenshot_dir = unreal.Paths.screenshot_dir()
            filename = f"{screenshot_dir}{filename}"

        unreal.AutomationLibrary.take_high_res_screenshot(
            res_x, res_y, filename
        )
        return {"success": True, "path": filename, "resolution": f"{res_x}x{res_y}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def take_screenshot_console(resolution="1920x1080"):
    """콘솔 커맨드로 스크린샷을 촬영한다 (간단한 방법)."""
    try:
        unreal.SystemLibrary.execute_console_command(None, f"HighResShot {resolution}")
        screenshot_dir = unreal.Paths.screenshot_dir()
        return {"success": True, "screenshot_dir": screenshot_dir}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_screenshot_dir():
    """스크린샷 저장 디렉토리 경로를 반환한다."""
    try:
        return {"path": unreal.Paths.screenshot_dir()}
    except Exception as e:
        return {"success": False, "error": str(e)}
