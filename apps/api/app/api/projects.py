from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.db_models import Detection, Project, User
from app.schemas import PaginatedResponse, ProjectCreate, ProjectResponse, ProjectUpdate


router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", status_code=201)
def create_project(data: ProjectCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    proj = Project(user_id=user.id, name=data.name, description=data.description)
    db.add(proj)
    db.flush()
    return {"success": True, "data": ProjectResponse.model_validate(proj).model_dump(mode="json"), "meta": {"request_id": "-"}}


@router.get("")
def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(Project).where(Project.user_id == user.id).order_by(desc(Project.created_at))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.execute(query.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return {"success": True, "data": {"items": [ProjectResponse.model_validate(p).model_dump(mode="json") for p in items], "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size}, "meta": {"request_id": "-"}}


@router.get("/{project_id}")
def get_project(project_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    proj = db.get(Project, project_id)
    if not proj or proj.user_id != user.id:
        raise HTTPException(404, "Project not found")
    return {"success": True, "data": ProjectResponse.model_validate(proj).model_dump(mode="json"), "meta": {"request_id": "-"}}


@router.patch("/{project_id}")
def update_project(project_id: str, data: ProjectUpdate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    proj = db.get(Project, project_id)
    if not proj or proj.user_id != user.id:
        raise HTTPException(404, "Project not found")
    if data.name is not None:
        proj.name = data.name
    if data.description is not None:
        proj.description = data.description
    db.flush()
    return {"success": True, "data": ProjectResponse.model_validate(proj).model_dump(mode="json"), "meta": {"request_id": "-"}}


@router.delete("/{project_id}")
def delete_project(project_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    proj = db.get(Project, project_id)
    if not proj or proj.user_id != user.id:
        raise HTTPException(404, "Project not found")
    db.delete(proj)
    db.commit()
    return {"success": True, "meta": {"request_id": "-"}}