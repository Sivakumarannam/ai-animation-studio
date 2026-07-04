from typing import Any

from packages.core.exceptions import PluginError
from plugins.base_plugin import ContentPlugin


class PluginRegistry:
    """
    Central registry for all content plugins.
    Follows the Open/Closed Principle — adding a plugin never changes this class.
    """

    def __init__(self) -> None:
        self._plugins: dict[str, ContentPlugin] = {}

    def register(self, plugin: ContentPlugin) -> None:
        meta = plugin.metadata
        if meta.id in self._plugins:
            raise PluginError(meta.id, f"Plugin '{meta.id}' is already registered")
        self._plugins[meta.id] = plugin

    def get(self, plugin_id: str) -> ContentPlugin:
        plugin = self._plugins.get(plugin_id)
        if plugin is None:
            raise PluginError(plugin_id, f"Plugin '{plugin_id}' is not registered")
        return plugin

    def get_plugin(self, plugin_id: str) -> ContentPlugin | None:
        """Non-raising alias — returns None if plugin not found."""
        return self._plugins.get(plugin_id)

    def list_plugins(self) -> list[dict[str, Any]]:
        return [
            {
                "id": p.metadata.id,
                "name": p.metadata.name,
                "version": p.metadata.version,
                "description": p.metadata.description,
                "language": p.metadata.language,
                "animation_style": p.metadata.animation_style,
                "tags": p.metadata.tags,
            }
            for p in self._plugins.values()
        ]

    def is_registered(self, plugin_id: str) -> bool:
        return plugin_id in self._plugins


_registry: PluginRegistry | None = None


def get_registry() -> PluginRegistry:
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry
