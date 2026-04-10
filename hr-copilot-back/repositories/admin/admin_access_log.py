from sqlalchemy.ext.asyncio import AsyncSession

from models.admin.admin_access_log import AdminAccessLog
from repositories.base_repository import BaseRepository


class AdminAccessLogRepository(BaseRepository[AdminAccessLog]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, AdminAccessLog)

    async def create_log(
        self,
        admin_id: int,
        action_type: str,
        action_target: str,
        target_id: str,
        result_tf: str,
        message: str,
    ) -> AdminAccessLog:
        entity = AdminAccessLog(
            admin_id=admin_id,
            action_type=action_type,
            action_target=action_target,
            target_id=target_id,
            result_tf=result_tf,
            message=message,
        )
        await self.add(entity)
        return entity