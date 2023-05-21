from typing import Any, Callable, Dict, List, Literal, Optional, Type, Union

from sqlalchemy.engine.interfaces import IsolationLevel, _ExecuteOptions, _ParamStyle
from sqlalchemy.log import _EchoFlagType
from sqlalchemy.pool import Pool, _CreatorFnType, _CreatorWRecFnType, _ResetStyleArgType
from typing_extensions import TypedDict


class EngineOptions(TypedDict, total=False):
    connect_args: Dict[Any, Any]
    convert_unicode: bool
    creator: Union[_CreatorFnType, _CreatorWRecFnType]
    echo: _EchoFlagType
    echo_pool: _EchoFlagType
    enable_from_linting: bool
    execution_options: _ExecuteOptions
    future: Literal[True]
    hide_parameters: bool
    implicit_returning: Literal[True]
    insertmanyvalues_page_size: int
    isolation_level: IsolationLevel
    json_deserializer: Callable[..., Any]
    json_serializer: Callable[..., Any]
    label_length: Optional[int]
    logging_name: str
    max_identifier_length: Optional[int]
    max_overflow: int
    module: Optional[Any]
    paramstyle: Optional[_ParamStyle]
    pool: Optional[Pool]
    poolclass: Optional[Type[Pool]]
    pool_logging_name: str
    pool_pre_ping: bool
    pool_size: int
    pool_recycle: int
    pool_reset_on_return: Optional[_ResetStyleArgType]
    pool_timeout: float
    pool_use_lifo: bool
    plugins: List[str]
    query_cache_size: int
    use_insertmanyvalues: bool
    kwargs: Dict[str, Any]
