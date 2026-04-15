import math
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password
from models.manager import Manager
from repositories.manager_repository import ManagerRepository
from schemas.manager import ManagerCreateRequest, ManagerListResponse, ManagerUpdateRequest, ManagerResponse


class ManagerService:
    @staticmethod
    async def create_manager(
        db: AsyncSession,
        request: ManagerCreateRequest,
        actor_id: int | None,
    ) -> ManagerResponse:
        repo = ManagerRepository(db)
        existing = await repo.find_by_login_id(request.login_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 로그인 ID 입니다.",
            )

        entity = Manager(
            login_id=request.login_id,
            password=hash_password(request.password),
            name=request.name,
            email=request.email,
            role_type=request.role_type,
            status=request.status,
            created_by=actor_id,
        )
        await repo.add(entity)
        await repo.flush()
        await db.commit()
        await repo.refresh(entity)
        return ManagerResponse.from_entity(entity)

    @staticmethod
    async def get_manager_list(
        db: AsyncSession,
        page: int,
        size: int,
        keyword: str | None = None,
        status_value: str | None = None,
        role_type: str | None = None,
    ) -> ManagerListResponse:
        repo = ManagerRepository(db)
        total_count = await repo.count_list(
            keyword=keyword,
            status=status_value,
            role_type=role_type,
        )
        rows = await repo.find_list(
            page=page,
            size=size,
            keyword=keyword,
            status=status_value,
            role_type=role_type,
        )
        total_pages = math.ceil(total_count / size) if total_count else 0
        return ManagerListResponse.of(
            items=[ManagerResponse.from_entity(row) for row in rows],
            total_count=total_count,
            total_pages=total_pages,
        )

    @staticmethod
    async def get_manager_detail(db: AsyncSession, manager_id: int) -> ManagerResponse:
        repo = ManagerRepository(db)
        entity = await repo.find_by_id_not_deleted(manager_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자 계정을 찾을 수 없습니다.",
            )
        return ManagerResponse.from_entity(entity)

    @staticmethod
    async def update_manager(
        db: AsyncSession,
        manager_id: int,
        request: ManagerUpdateRequest,
    ) -> ManagerResponse:
        repo = ManagerRepository(db)
        entity = await repo.find_by_id_not_deleted(manager_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자 계정을 찾을 수 없습니다.",
            )

        entity.name = request.name
        entity.email = request.email
        entity.role_type = request.role_type
        entity.status = request.status

        if request.password:
            entity.password = hash_password(request.password)

        await db.commit()
        await repo.refresh(entity)
        return ManagerResponse.from_entity(entity)

    @staticmethod
    async def update_manager_status(
        db: AsyncSession,
        manager_id: int,
        status_value: str,
    ) -> ManagerResponse:
        repo = ManagerRepository(db)
        entity = await repo.find_by_id_not_deleted(manager_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자 계정을 찾을 수 없습니다.",
            )

        entity.status = status_value
        await db.commit()
        await repo.refresh(entity)
        return ManagerResponse.from_entity(entity)

    @staticmethod
    async def delete_manager(
        db: AsyncSession,
        manager_id: int,
        actor_id: int | None,
    ) -> None:
        repo = ManagerRepository(db)
        entity = await repo.find_by_id_not_deleted(manager_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자 계정을 찾을 수 없습니다.",
            )

        entity.deleted_at = datetime.now(timezone.utc)
        entity.deleted_by = actor_id
        await db.commit()
