from sqlalchemy.types import VARCHAR
from sqlmodel import Column, Field, SQLModel


class PlayerInfo(SQLModel, table=True):
    __tablename__: str = 'minecraft_player_info'
    id: int | None = Field(default=None, primary_key=True, nullable=False)
    qq: str = Field(max_length=12, nullable=False, index=True)
    join_time: int | None = Field(default=None, nullable=True)
    leave_time: int | None = Field(default=None, nullable=True)
    uuid1: str | None = Field(
        sa_column=Column(VARCHAR(32), index=True, nullable=True, default=None), nullable=True, default=None
    )
    uuid1_add_time: int | None = Field(default=None, nullable=True)
    uuid2: str | None = Field(
        sa_column=Column(VARCHAR(32), index=True, nullable=True, default=None), nullable=True, default=None
    )
    uuid2_add_time: int | None = Field(default=None, nullable=True)
    blocked: bool = Field(default=False)
    block_reason: str | None = Field(default=None, nullable=True)
