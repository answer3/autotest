def video_key(run_id: int, video_name: str) -> str:
    return f"videos/{run_id}/{video_name}"


def screenshot_key(run_id: int, image_name: str) -> str:
    return f"screenshots/{run_id}/{image_name}"
