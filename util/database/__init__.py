#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from asyncio import Semaphore
from typing import Optional

from loguru import logger
from sqlalchemy.engine.result import Result, Row
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.base import Executable
from sqlmodel import SQLModel

from ..config import basic_cfg
from .models import *

# sqlite_url = 'sqlite+aiosqlite:///data/redbot.db'
# mysql_url = 'mysql+asyncmy://user:pass@hostname/dbname?charset=utf8mb4


class Database:

    lock: Optional[Semaphore] = None
    engine: AsyncEngine
    # Session: sessionmaker[AsyncSession]  # 不可取消注释，该类型注释仅给人看

    @classmethod
    async def init(cls, debug: bool = False) -> None:
        if basic_cfg.databaseUrl.startswith('sqlite'):
            cls.lock = Semaphore(1)
        cls.engine = create_async_engine(basic_cfg.databaseUrl, echo=debug, future=True)
        async with cls.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        cls.Session = sessionmaker(cls.engine, class_=AsyncSession, expire_on_commit=False)

    @classmethod
    async def exec(cls, sql: Executable) -> Optional[Result]:
        async with cls.Session() as session:
            # if cls.lock:
            #     await cls.lock.acquire()
            try:
                result = await session.execute(sql)
                await session.commit()
                return result
            except Exception as e:
                logger.exception(e)
                await session.rollback()
            # finally:
            #     if cls.lock and cls.lock.locked():
            #         cls.lock.release()

    @classmethod
    async def exec_read(cls, sql: Executable) -> Result:
        """Only for read operation"""
        async with cls.Session() as session:
            result = await session.execute(sql)
            return result

    @classmethod
    async def select_all(cls, sql: Executable) -> list[Row]:
        result = await cls.exec_read(sql)
        return result.all()

    @classmethod
    async def select_first(cls, sql: Executable) -> Row | None:
        result = await cls.exec_read(sql)
        return result.first()

    @classmethod
    async def add(cls, row: SQLModel) -> bool:
        async with cls.Session() as session:
            session.add(row)
            # if cls.lock:
            #     await cls.lock.acquire()
            try:
                await session.commit()
                await session.refresh(row)
                return True
            except Exception as e:
                logger.exception(e)
                await session.rollback()
                return False
            # finally:
            #     if cls.lock and cls.lock.locked():
            #         cls.lock.release()

    @classmethod
    async def add_many(cls, *rows: SQLModel) -> bool:
        async with cls.Session() as session:
            for row in rows:
                session.add(row)
            # if cls.lock:
            #     await cls.lock.acquire()
            try:
                await session.commit()
                for row in rows:
                    await session.refresh(row)
                return True
            except Exception as e:
                logger.exception(e)
                await session.rollback()
                return False
            # finally:
            #     if cls.lock and cls.lock.locked():
            #         cls.lock.release()

    @classmethod
    async def update_exist(cls, row: SQLModel) -> bool:
        return await cls.add(row)

    @classmethod
    async def delete_exist(cls, row: SQLModel) -> bool:
        async with cls.Session() as session:
            # if cls.lock:
            #     await cls.lock.acquire()
            try:
                await session.delete(row)
                await session.commit()
                return True
            except Exception as e:
                logger.exception(e)
                await session.rollback()
                return False
            # finally:
            #     if cls.lock and cls.lock.locked():
            #         cls.lock.release()

    @classmethod
    async def delete_many_exist(cls, *rows: SQLModel) -> bool:
        async with cls.Session() as session:
            # if cls.lock:
            #     await cls.lock.acquire()
            try:
                for row in rows:
                    await session.delete(row)
                await session.commit()
                return True
            except Exception as e:
                logger.exception(e)
                await session.rollback()
                return False
            # finally:
            #     if cls.lock and cls.lock.locked():
            #         cls.lock.release()
