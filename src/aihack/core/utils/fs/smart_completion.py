"""Smart directory mapping and path segment expansion for advanced file completion."""
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .file_index import FileSystemIndex, get_file_index


@dataclass
class DirectoryMapping:
    """Represents a smart directory mapping."""

    shortcut: str
    target_path: str
    confidence: float
    usage_count: int = 0


@dataclass
class PathExpansionState:
    """State for incremental path expansion."""

    original_query: str
    current_path: str
    available_segments: List[str]
    segment_index: int
    is_complete: bool = False


class SmartDirectoryMapper:
    """Maps shortcuts to directories with learning from project structure."""

    def __init__(self) -> None:
        self.file_index: Optional[FileSystemIndex] = None
        self.static_mappings = self._get_static_mappings()
        self.learned_mappings: Dict[str, DirectoryMapping] = {}
        self.usage_stats: Counter = Counter()

    async def initialize(self) -> None:
        """Initialize the mapper with project analysis."""
        self.file_index = await get_file_index()
        await self._analyze_project_structure()

    def _get_static_mappings(self) -> Dict[str, str]:
        """Get static directory mappings for common patterns."""
        return {
            # Core framework directories
            "cli": "src/aihack/cli/",
            "core": "src/aihack/core/",
            "models": "src/aihack/models/",
            "safety": "src/aihack/safety/",
            "utils": "src/aihack/core/utils/",
            "runners": "src/aihack/cli/runners/",
            # Standard project directories
            "src": "src/",
            "tests": "tests/",
            "test": "tests/",
            "docs": "docs/",
            "doc": "docs/",
            "scripts": "scripts/",
            "script": "scripts/",
            "config": "config/",
            "configs": "config/",
            # Common subdirectories
            "tasks": "src/aihack/tasks/",
            "session": "src/aihack/cli/",
            "context": "src/aihack/core/",
        }

    async def _analyze_project_structure(self) -> None:
        """Analyze project structure to discover patterns."""
        if not self.file_index:
            return

        # Analyze directory names and create smart mappings
        directory_names = defaultdict(list)

        # Collect all directory names and their paths
        for dir_path in self.file_index.directories.keys():
            if not dir_path:  # Skip root
                continue

            # Extract directory name components
            parts = dir_path.split("/")
            for part in parts:
                if part:
                    directory_names[part.lower()].append(dir_path)

        # Create mappings for directories that appear frequently
        for name, paths in directory_names.items():
            if len(paths) == 1:  # Unique directory name
                confidence = 1.0
            elif len(paths) <= 3:  # Few conflicts
                confidence = 0.8
            else:  # Many conflicts, lower confidence
                confidence = 0.5

            # Prefer shorter paths
            best_path = min(paths, key=len)

            # Don't override static mappings
            if name not in self.static_mappings:
                self.learned_mappings[name] = DirectoryMapping(
                    shortcut=name, target_path=best_path + "/", confidence=confidence
                )

    def get_mapping(self, shortcut: str) -> Optional[str]:
        """Get directory mapping for a shortcut."""
        shortcut_lower = shortcut.lower()

        # Check static mappings first
        if shortcut_lower in self.static_mappings:
            self.usage_stats[shortcut_lower] += 1
            return self.static_mappings[shortcut_lower]

        # Check learned mappings
        if shortcut_lower in self.learned_mappings:
            mapping = self.learned_mappings[shortcut_lower]
            mapping.usage_count += 1
            self.usage_stats[shortcut_lower] += 1
            return mapping.target_path

        return None

    def get_fuzzy_mappings(
        self, partial: str, limit: int = 5
    ) -> List[Tuple[str, str, float]]:
        """Get fuzzy matches for partial shortcuts."""
        partial_lower = partial.lower()
        matches = []

        # Check static mappings
        for shortcut, path in self.static_mappings.items():
            if shortcut.startswith(partial_lower):
                score = len(partial_lower) / len(shortcut)
                usage_boost = self.usage_stats.get(shortcut, 0) * 0.1
                matches.append((shortcut, path, score + usage_boost))

        # Check learned mappings
        for mapping in self.learned_mappings.values():
            if mapping.shortcut.startswith(partial_lower):
                score = len(partial_lower) / len(mapping.shortcut)
                usage_boost = mapping.usage_count * 0.05
                confidence_boost = mapping.confidence * 0.1
                final_score = score + usage_boost + confidence_boost
                matches.append((mapping.shortcut, mapping.target_path, final_score))

        # Sort by score and return top matches
        matches.sort(key=lambda x: x[2], reverse=True)
        return matches[:limit]

    def learn_mapping(self, shortcut: str, target_path: str) -> None:
        """Learn a new mapping from user behavior."""
        shortcut_lower = shortcut.lower()

        if shortcut_lower not in self.static_mappings:
            self.learned_mappings[shortcut_lower] = DirectoryMapping(
                shortcut=shortcut_lower,
                target_path=target_path,
                confidence=0.6,
                usage_count=1,
            )


class PathSegmentExpander:
    """Handles incremental path expansion with tab navigation."""

    def __init__(self) -> None:
        self.file_index: Optional[FileSystemIndex] = None
        self.expansion_states: Dict[str, PathExpansionState] = {}

    async def initialize(self) -> None:
        """Initialize the expander."""
        self.file_index = await get_file_index()

    def create_expansion_state(self, query: str) -> PathExpansionState:
        """Create expansion state for a query."""
        segments = self._get_available_segments(query)

        state = PathExpansionState(
            original_query=query,
            current_path=query,
            available_segments=segments,
            segment_index=0,
        )

        self.expansion_states[query] = state
        return state

    def _get_available_segments(self, query: str) -> List[str]:
        """Get available path segments for expansion."""
        if not self.file_index:
            return []

        # Get fuzzy matches and extract unique path prefixes
        matches = self.file_index.get_fuzzy_matches(query, limit=20)

        segments = []
        seen = set()

        for path, _ in matches:
            if path.startswith(query):
                # Extract the next segment after the query
                remaining = path[len(query) :].lstrip("/")
                if remaining:
                    if "/" in remaining:
                        next_segment = remaining.split("/")[0]
                        full_segment = query + "/" + next_segment
                    else:
                        full_segment = path

                    if full_segment not in seen:
                        seen.add(full_segment)
                        segments.append(full_segment)

        return sorted(segments)

    def expand_next_segment(self, state: PathExpansionState) -> Optional[str]:
        """Expand to next available segment."""
        if state.segment_index >= len(state.available_segments):
            state.segment_index = 0  # Wrap around

        if not state.available_segments:
            return None

        next_path = state.available_segments[state.segment_index]
        state.current_path = next_path
        state.segment_index += 1

        # Check if this is a complete file/directory
        if self.file_index:
            state.is_complete = self.file_index.path_exists(next_path)

        return next_path

    def expand_to_directory(self, query: str) -> Optional[str]:
        """Expand query to next directory level."""
        if not self.file_index:
            return None

        # Look for directories that start with query
        matches = self.file_index.get_fuzzy_matches(query, limit=10)

        for path, score in matches:
            if path.startswith(query) and self.file_index.is_directory(
                path.rstrip("/")
            ):
                # Find next directory boundary
                remaining = path[len(query) :].lstrip("/")
                if "/" in remaining:
                    next_dir = remaining.split("/")[0]
                    return query + "/" + next_dir + "/"
                else:
                    return path if path.endswith("/") else path + "/"

        return None

    def complete_path(self, query: str, prefer_files: bool = False) -> Optional[str]:
        """Complete path to best match."""
        if not self.file_index:
            return None

        matches = self.file_index.get_fuzzy_matches(query, limit=5)

        if not matches:
            return None

        # Filter based on preference
        if prefer_files:
            file_matches = [
                (path, score) for path, score in matches if not path.endswith("/")
            ]
            if file_matches:
                return file_matches[0][0]

        return matches[0][0]

    def get_completion_suggestions(
        self, query: str, limit: int = 8
    ) -> List[Dict[str, Any]]:
        """Get formatted completion suggestions."""
        if not self.file_index:
            return []

        matches = self.file_index.get_fuzzy_matches(query, limit=limit)
        suggestions = []

        for i, (path, score) in enumerate(matches):
            is_directory = path.endswith("/") or self.file_index.is_directory(path)

            # Determine suggestion type
            if path.startswith(query):
                if is_directory and not path.endswith("/"):
                    suggestion_type = "directory_expansion"
                    display_path = path + "/"
                else:
                    suggestion_type = "exact_match"
                    display_path = path
            else:
                suggestion_type = "fuzzy_match"
                display_path = path

            suggestions.append(
                {
                    "path": path,
                    "display_path": display_path,
                    "score": score,
                    "is_directory": is_directory,
                    "suggestion_type": suggestion_type,
                    "icon": "📁" if is_directory else "📄",
                }
            )

        return suggestions


# Enhanced completion coordinator
class AdvancedFileCompletion:
    """Coordinates all completion components for unified experience."""

    def __init__(self) -> None:
        self.directory_mapper = SmartDirectoryMapper()
        self.path_expander = PathSegmentExpander()
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize all completion components."""
        if self.initialized:
            return

        await self.directory_mapper.initialize()
        await self.path_expander.initialize()
        self.initialized = True

    async def get_smart_suggestions(
        self, query: str, completion_type: str = "auto", limit: int = 8
    ) -> List[Dict[str, Any]]:
        """Get smart suggestions based on query type."""
        if not self.initialized:
            await self.initialize()

        suggestions = []

        # Try directory mapping first for simple queries
        if "/" not in query and len(query) <= 10:
            mapping = self.directory_mapper.get_mapping(query)
            if mapping:
                # Get files in mapped directory
                file_index = await get_file_index()
                dir_files = file_index.get_files_in_directory(mapping.rstrip("/"))

                for file_path in dir_files[: limit // 2]:
                    suggestions.append(
                        {
                            "path": file_path,
                            "display_path": file_path,
                            "score": 1.0,
                            "is_directory": file_path.endswith("/"),
                            "suggestion_type": "directory_mapped",
                            "icon": "📁" if file_path.endswith("/") else "📄",
                        }
                    )

        # Add path expansion suggestions
        path_suggestions = self.path_expander.get_completion_suggestions(query, limit)
        suggestions.extend(path_suggestions)

        # Remove duplicates and sort by score
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            path = suggestion["path"]
            if path not in seen:
                seen.add(path)
                unique_suggestions.append(suggestion)

        unique_suggestions.sort(key=lambda x: x["score"], reverse=True)  # type: ignore[return-value,arg-type]
        return unique_suggestions[:limit]
