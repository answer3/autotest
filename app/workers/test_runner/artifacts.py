from pathlib import Path


def run_video_dir(artifacts_root: Path, run_id: int) -> Path:
    """artifacts/videos/<run_id>/"""
    return artifacts_root / "videos" / str(run_id)


def run_screenshot_dir(artifacts_root: Path, run_id: int) -> Path:
    """artifacts/screenshots/<run_id>/"""
    return artifacts_root / "screenshots" / str(run_id)


def video_path(artifacts_root: Path, run_id: int, video_name: str) -> Path:
    """artifacts/videos/<run_id>/<video_name>"""
    return run_video_dir(artifacts_root, run_id) / video_name


def screenshot_path(artifacts_root: Path, run_id: int, image_name: str) -> Path:
    """artifacts/screenshots/<run_id>/<image_name>"""
    return run_screenshot_dir(artifacts_root, run_id) / image_name


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
