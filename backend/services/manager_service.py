"""관리자 계정 관리 서비스를 제공한다.

관리자 생성, 조회, 수정, 삭제를 담당한다.
계정 정보 자체보다 운영 규칙을 지키는 것이 중요하므로,
중복 로그인 ID 확인과 소프트 삭제 처리를 서비스 레이어에서 보장한다.
"""

import math
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password
from models.manager import Manager
from repositories.manager_repository import ManagerRepository
from schemas.manager import ManagerCreateRequest, ManagerListResponse, ManagerUpdateRequest, ManagerResponse


class ManagerService:
    """관리자 계정 CRUD를 담당하는 서비스다."""

    @staticmethod
    async def create_manager(
        db: AsyncSession,
        request: ManagerCreateRequest,
        actor_id: int | None,
    ) -> ManagerResponse:
        """관리자 계정을 생성한다.

        로그인 ID는 유일해야 하므로 생성 전에 먼저 중복을 확인한다.
        비밀번호는 항상 해시한 값만 저장한다.
        """
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
        """검색 조건에 맞는 관리자 목록과 페이지 정보를 반환한다."""
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
        """삭제되지 않은 관리자 상세 정보를 반환한다."""
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
        """관리자 기본 정보를 수정한다.

        비밀번호는 값이 들어온 경우에만 갱신한다.
        빈 비밀번호로 기존 값을 지우지 않도록 하는 것이 기준이다.
        """
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
        """관리자 상태만 빠르게 변경한다."""
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
        """관리자 계정을 소프트 삭제한다.

        실제 레코드를 지우지 않고 삭제 시각과 삭제자를 남겨
        운영 이력과 감사 추적을 유지한다.
        """
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
