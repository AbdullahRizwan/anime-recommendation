import asyncio

from src.infrastructure.anime_repository import AnimeRepository


class _FakeResult:
    def scalars(self) -> "_FakeResult":
        return self

    def all(self) -> list:
        return []

    def scalar_one_or_none(self) -> None:
        return None


class _ConcurrencyGuardSession:
    """Stand-in AsyncSession that records the peak number of overlapping ops.

    A real AsyncSession raises when two coroutines use it at once; here we just
    measure overlap so the test can assert the repository serialises access.
    """

    def __init__(self) -> None:
        self._current = 0
        self.max_concurrent = 0

    async def _op(self) -> None:
        self._current += 1
        self.max_concurrent = max(self.max_concurrent, self._current)
        await asyncio.sleep(0.01)  # yield so any unguarded overlap shows up
        self._current -= 1

    async def execute(self, *args: object, **kwargs: object) -> _FakeResult:
        await self._op()
        return _FakeResult()

    async def merge(self, *args: object, **kwargs: object) -> None:
        await self._op()

    async def commit(self, *args: object, **kwargs: object) -> None:
        await self._op()


async def test_repository_serialises_concurrent_session_access() -> None:
    """Parallel tool calls share one session; the repo lock must serialise them."""
    session = _ConcurrencyGuardSession()
    repo = AnimeRepository(session)  # type: ignore[arg-type]

    await asyncio.gather(
        repo.get_search_cache("a"),
        repo.get_search_cache("b"),
        repo.get_seasonal("SPRING", 2026),
        repo.store_search_cache("c", []),
    )

    assert session.max_concurrent == 1
