import asyncio
from app.config.database import engine
from app.models.base import Base
import app.models.document
import app.models.chunk
import app.models.conversation
import app.models.rag_run
import app.models.evaluation
import app.models.user
from app.config.database import async_session_factory
from app.repositories.user_repository import UserRepository
from app.models.user import UserRole


async def init_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables initialized successfully.")

    # Seed default HR and Employee accounts if not present
    async with async_session_factory() as session:
        repo = UserRepository(session)
        hr_user = await repo.get_by_email("hr@company.com")
        if not hr_user:
            await repo.create_user(
                email="hr@company.com",
                password="hr123456",
                full_name="HR Administrator",
                role=UserRole.HR,
            )
            print("Seeded default HR user: hr@company.com / hr123456")

        emp_user = await repo.get_by_email("employee@company.com")
        if not emp_user:
            await repo.create_user(
                email="employee@company.com",
                password="employee123456",
                full_name="John Doe (Employee)",
                role=UserRole.EMPLOYEE,
            )
            print("Seeded default Employee user: employee@company.com / employee123456")


if __name__ == "__main__":
    asyncio.run(init_tables())
