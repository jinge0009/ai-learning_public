import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 从环境变量读取数据库地址（如果在本地跑，用 SQLite 兜底）
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 获取数据库会话的依赖函数（给 FastAPI 用）
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()