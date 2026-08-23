"""Background AI controller that keeps search work out of Pygame's event loop."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from threading import Event

from ..logic import GameState, Position
from .api import SearchLimits, SearchResult, choose_move


@dataclass(frozen=True)
class AICompletion:
    request_id: int
    source_moves: tuple[Position, ...]
    result: SearchResult


class AIController:
    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="gomoku-ai")
        self._future: Future[AICompletion] | None = None
        self._cancel = Event()
        self._request_id = 0

    @property
    def thinking(self) -> bool:
        return self._future is not None

    def start(self, state: GameState, limits: SearchLimits | None = None) -> int:
        self.cancel()
        self._request_id += 1
        request_id = self._request_id
        source_moves = state.moves
        self._cancel = Event()
        cancel = self._cancel

        def work() -> AICompletion:
            result = choose_move(state, limits, cancel.is_set)
            return AICompletion(request_id, source_moves, result)

        self._future = self._executor.submit(work)
        return request_id

    def poll(self) -> AICompletion | None:
        future = self._future
        if future is None or not future.done():
            return None
        self._future = None
        if future.cancelled():
            return None
        completion = future.result()
        return completion if completion.request_id == self._request_id else None

    def cancel(self) -> None:
        self._request_id += 1
        self._cancel.set()
        if self._future is not None:
            self._future.cancel()
            self._future = None

    def close(self) -> None:
        self.cancel()
        self._executor.shutdown(wait=False, cancel_futures=True)
