from datetime import datetime, timezone
from math import ceil

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password
from models.admin import Admin
from repositories.admin.admin_repository import AdminRepository
from repositories.admin.admin_access_log import AdminAccessLogRepository
from schemas.admin.admin import AdminListResponse, AdminRequest, AdminResponse

class AdminService:
    @staticmethod
    async def create_admin(
        db: AsyncSession,
        request: AdminRequest,
        actor_login_id: str,
    ) -> AdminResponse:
        admin_repo = AdminRepository(db)
        log_repo = AdminAccessLogRepository(db)

        existing = await admin_repo.find_by_login_id(request.login_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 loginId 입니다.",
            )

        if not request.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="등록 시 password 는 필수입니다.",
            )

        entity = Admin(
            group_id=request.group_id,
            login_id=request.login_id,
            password_hash=hash_password(request.password),
            name=request.name,
            email=request.email,
            status=request.status or "ACTIVE",
            use_tf=request.use_tf or "Y",
            del_tf=request.del_tf or "N",
            reg_adm=actor_login_id,
        )

        try:
            await admin_repo.add(entity)
            await admin_repo.flush()

            await log_repo.create_log(
                admin_id=entity.id,
                action_type="CREATE",
                action_target="admin",
                target_id=str(entity.id),
                result_tf="Y",
                message="관리자 등록",
            )

            await db.commit()
            await admin_repo.refresh(entity)
            return AdminResponse.from_entity(entity)

        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def get_admin_list(
        db: AsyncSession,
        page: int,
        size: int,
        keyword: str | None = None,
        status: str | None = None,
        use_tf: str | None = None,
    ) -> AdminListResponse:
        admin_repo = AdminRepository(db)

        total_count = await admin_repo.count_list(
            keyword=keyword,
            status=status,
            use_tf=use_tf,
        )
        rows = await admin_repo.find_list(
            page=page,
            size=size,
            keyword=keyword,
            status=status,
            use_tf=use_tf,
        )

        total_pages = ceil(total_count / size) if size > 0 else 1

        return AdminListResponse.of(
            items=[AdminResponse.from_entity(row) for row in rows],
            total_count=total_count,
            total_pages=total_pages,
        )

    @staticmethod
    async def get_admin_detail(
        db: AsyncSession,
        admin_id: int,
    ) -> AdminResponse:
        admin_repo = AdminRepository(db)

        entity = await admin_repo.find_by_id_not_deleted(admin_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자 정보를 찾을 수 없습니다.",
            )

        return AdminResponse.from_entity(entity)

    @staticmethod
    async def update_admin(
        db: AsyncSession,
        admin_id: int,
        request: AdminRequest,
        actor_login_id: str,
    ) -> AdminResponse:
        admin_repo = AdminRepository(db)
        log_repo = AdminAccessLogRepository(db)

        entity = await admin_repo.find_by_id_not_deleted(admin_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자 정보를 찾을 수 없습니다.",
            )

        if request.login_id != entity.login_id:
            dup = await admin_repo.find_by_login_id_excluding_id(
                login_id=request.login_id,
                admin_id=admin_id,
            )
            if dup:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="이미 사용 중인 loginId 입니다.",
                )

        entity.group_id = request.group_id
        entity.login_id = request.login_id
        entity.name = request.name
        entity.email = request.email
        entity.status = request.status or entity.status
        entity.use_tf = request.use_tf or entity.use_tf
        entity.del_tf = request.del_tf or entity.del_tf
        entity.up_adm = actor_login_id
        entity.up_date = datetime.now(timezone.utc).replace(tzinfo=None)

        if request.password:
            entity.password_hash = hash_password(request.password)

        try:
            await log_repo.create_log(
                admin_id=entity.id,
                action_type="UPDATE",
                action_target="admin",
                target_id=str(entity.id),
                result_tf="Y",
                message="관리자 수정",
            )

            await db.commit()
            await admin_repo.refresh(entity)
            return AdminResponse.from_entity(entity)

        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def delete_admin(
        db: AsyncSession,
        admin_id: int,
        actor_login_id: str,
    ) -> None:
        admin_repo = AdminRepository(db)
        log_repo = AdminAccessLogRepository(db)

        entity = await admin_repo.find_by_id_not_deleted(admin_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자 정보를 찾을 수 없습니다.",
            )

        entity.del_tf = "Y"
        entity.del_adm = actor_login_id
        entity.del_date = datetime.now(timezone.utc).replace(tzinfo=None)

        try:
            await log_repo.create_log(
                admin_id=entity.id,
                action_type="DELETE",
                action_target="admin",
                target_id=str(entity.id),
                result_tf="Y",
                message="관리자 삭제(soft delete)",
            )

            await db.commit()

        except Exception:
            await db.rollback()
            raise