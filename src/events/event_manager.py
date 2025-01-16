from typing import Dict, Set, Callable, Any, Coroutine
import logging
import asyncio
from datetime import datetime
from .event_types import EventType

logger = logging.getLogger(__name__)


class EventManager:
    def __init__(self):
        self._subscribers: Dict[EventType, Set[Callable]] = {
            event_type: set() for event_type in EventType
        }
        self._event_history: Dict[EventType, list] = {
            event_type: [] for event_type in EventType
        }
        self._max_history = 1000  # Maximum events to keep in history per type

    async def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """Subscribe to an event type"""
        try:
            self._subscribers[event_type].add(callback)
            logger.debug(f"Subscribed to {event_type.value}")
        except Exception as e:
            logger.error(f"Error subscribing to {event_type.value}: {str(e)}")
            raise

    async def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """Unsubscribe from an event type"""
        try:
            self._subscribers[event_type].discard(callback)
            logger.debug(f"Unsubscribed from {event_type.value}")
        except Exception as e:
            logger.error(
                f"Error unsubscribing from {event_type.value}: {str(e)}")
            raise

    async def emit(self, event_type: EventType, data: Dict[str, Any]) -> None:
        """Emit an event to all subscribers"""
        try:
            # Add timestamp to event data
            event_data = {
                **data,
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type.value
            }

            # Store in history
            self._event_history[event_type].append(event_data)
            if len(self._event_history[event_type]) > self._max_history:
                self._event_history[event_type].pop(0)

            # Notify subscribers
            tasks = []
            for callback in self._subscribers[event_type]:
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(asyncio.create_task(callback(event_data)))
                else:
                    tasks.append(asyncio.create_task(
                        asyncio.to_thread(callback, event_data)))

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Error emitting event {event_type.value}: {str(e)}")
            raise

    async def get_event_history(
        self,
        event_type: EventType,
        limit: int = 100
    ) -> list:
        """Get historical events for a specific type"""
        try:
            history = self._event_history[event_type]
            return history[-limit:] if limit else history
        except Exception as e:
            logger.error(
                f"Error getting history for {event_type.value}: {str(e)}")
            raise

    async def clear_history(self, event_type: EventType = None) -> None:
        """Clear event history for specific type or all types"""
        try:
            if event_type:
                self._event_history[event_type].clear()
            else:
                for event_list in self._event_history.values():
                    event_list.clear()
        except Exception as e:
            logger.error(f"Error clearing event history: {str(e)}")
            raise
