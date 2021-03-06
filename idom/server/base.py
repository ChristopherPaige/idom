import abc
from asyncio import AbstractEventLoop, new_event_loop, set_event_loop, get_event_loop
from typing import TypeVar, Dict, Any, Tuple, Type, Optional, Generic, TypeVar
from threading import Thread

from idom.core.element import ElementConstructor
from idom.core.layout import Layout, Layout
from idom.core.dispatcher import (
    AbstractDispatcher,
    SendCoroutine,
    RecvCoroutine,
)


_App = TypeVar("_App", bound=Any)
_Config = TypeVar("_Config", bound=Any)
_Self = TypeVar("_Self", bound="AbstractRenderServer[Any, Any]")


class AbstractRenderServer(Generic[_App, _Config]):
    """Base class for all IDOM server application and extension implementations.

    It is assumed that IDOM will be used in conjuction with some async-enabled server
    library (e.g. ``sanic`` or ``tornado``) so these server implementations should work
    standalone and as an extension to an existing application.

    Standalone usage:
        :meth:`AbstractServerExtension.run` or :meth:`AbstractServerExtension.daemon`
    Register an extension:
        :meth:`AbstractServerExtension.register`
    """

    _loop: AbstractEventLoop
    _dispatcher_type: Type[AbstractDispatcher]
    _layout_type: Type[Layout] = Layout

    def __init__(
        self,
        constructor: ElementConstructor,
        config: Optional[_Config] = None,
    ) -> None:
        self._app: Optional[_App] = None
        self._make_root_element = constructor
        self._daemonized = False
        self._config = self._init_config()
        if config is not None:
            self._config = self._update_config(self._config, config)

    @property
    def loop(self) -> AbstractEventLoop:
        return self._loop

    @property
    def application(self) -> _App:
        if self._app is None:
            raise RuntimeError("No application registered.")
        return self._app

    def run(self, *args: Any, **kwargs: Any) -> None:
        """Run as a standalone application."""
        self._loop = get_event_loop()
        if self._app is None:
            app = self._default_application(self._config)
            self.register(app)
        else:
            app = self._app
        return self._run_application(app, self._config, args, kwargs)

    def daemon(self, *args: Any, **kwargs: Any) -> Thread:
        """Run the standalone application in a seperate thread."""
        self._daemonized = True

        def run_in_thread() -> None:
            set_event_loop(new_event_loop())
            return self.run(*args, **kwargs)

        thread = Thread(target=run_in_thread, daemon=True)
        thread.start()
        return thread

    def register(self: _Self, app: Optional[_App]) -> _Self:
        """Register this as an extension."""
        self._setup_application(app, self._config)
        self._app = app
        return self

    def stop(self) -> None:
        """Stop the running application"""
        self.loop.call_soon_threadsafe(self._stop)

    @abc.abstractmethod
    def _stop(self) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def _init_config(self) -> _Config:
        """Return the default configuration options."""

    @abc.abstractmethod
    def _default_application(self, config: _Config) -> _App:
        """If used standalone this should return an application."""
        raise NotImplementedError()

    @abc.abstractmethod
    def _setup_application(self, app: _App, config: _Config) -> None:
        ...

    @abc.abstractmethod
    def _run_application(
        self, app: _App, config: _Config, args: Tuple[Any, ...], kwargs: Dict[str, Any]
    ) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def _update_config(self, old: _Config, new: _Config) -> _Config:  # pragma: no cover
        """Return the new configuration options

        Parameters:
            old: The existing configuration options
            new: The new configuration options
        """
        raise NotImplementedError()

    async def _run_dispatcher(
        self,
        send: SendCoroutine,
        recv: RecvCoroutine,
        params: Dict[str, Any],
    ) -> None:
        async with self._make_dispatcher(params) as dispatcher:
            await dispatcher.run(send, recv, None)

    def _make_dispatcher(
        self,
        params: Dict[str, Any],
    ) -> AbstractDispatcher:
        return self._dispatcher_type(self._make_layout(params))

    def _make_layout(
        self,
        params: Dict[str, Any],
    ) -> Layout:
        return self._layout_type(self._make_root_element(**params))
