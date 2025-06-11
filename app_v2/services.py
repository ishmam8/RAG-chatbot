from fastapi import HTTPException
from app_v2.config import Settings

def get_project_info(project_id):
    project_info = Settings.PROJECTS.get(project_id)
    if not project_info:
        raise HTTPException(status_code=404, detail="Project not found")
    return project_info["name"], project_info["intro"]