import asyncio
from typing import Any, Callable, Dict, List, TypeVar, Awaitable

T = TypeVar('T')

class EventBus:
    """
    Asynchronous, typed Event Bus for decoupled communication between components.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], Awaitable[None]]]] = {}

    def subscribe(self, event_type: str, callback: Callable[[Any], Awaitable[None]]):
        """
        Subscribe to an event type. The callback must be an async function.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    async def publish(self, event_type: str, data: Any):
        """
        Publish an event, calling all registered async callbacks concurrently.
        """
        if event_type in self._subscribers:
            callbacks = self._subscribers[event_type]
            await asyncio.gather(*(callback(data) for callback in callbacks))
