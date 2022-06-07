from typing import Any, Callable, Coroutine

from pydantic import BaseModel


class Route(BaseModel):
    path: str
    methods: list[str] = ['GET']
    endpoint: Callable[..., Coroutine[Any, Any, Any]]
    response_model: Any | None = None
    kwargs: dict = {}


class Router:
    routes: list[Route] = []

    @classmethod
    def register(cls, path: str, methods: list[str], response_model, **kwargs):
        def wrapper(func: Callable[..., Coroutine[Any, Any, Any]]):
            cls.routes.append(
                Route(path=path, methods=methods, endpoint=func, response_model=response_model, kwargs=kwargs)
            )
            return func

        return wrapper

    @classmethod
    def get(cls, path: str, response_model, **kwargs):
        return cls.register(path, ['GET'], response_model=response_model, **kwargs)

    @classmethod
    def post(cls, path: str, response_model, **kwargs):
        return cls.register(path, ['POST'], response_model=response_model, **kwargs)
