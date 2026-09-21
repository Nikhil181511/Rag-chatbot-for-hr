from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole
from app.config.security import hash_password


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email.lower().strip())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str = "",
        role: UserRole = UserRole.EMPLOYEE,
    ) -> User:
        hashed = hash_password(password)
        user = User(
            email=email.lower().strip(),
            hashed_password=hashed,
            full_name=full_name,
            role=role.value if isinstance(role, UserRole) else role,
            is_active=True,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def list_users(self, limit: int = 100) -> Sequence[User]:
        stmt = select(User).order_by(User.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
