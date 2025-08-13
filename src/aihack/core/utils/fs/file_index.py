"""High-performance file system indexing for smart file completion."""
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class FileEntry:
    """Represents a file in the index."""

    path: str
    size: int
    mtime: float
    is_dir: bool


@dataclass
class DirectoryEntry:
    """Represents a directory with its children."""

    path: str
    children: List[str]
    mtime: float


class FileSystemIndex:
    """High-performance file system cache with incremental updates."""

    def __init__(
        self, root_path: str = ".", max_depth: int = 3, max_files: int = 10000
    ):
        self.root_path = Path(root_path).resolve()
        self.max_depth = max_depth
        self.max_files = max_files

        # Core indexes
        self.files: Dict[str, FileEntry] = {}
        self.directories: Dict[str, DirectoryEntry] = {}
        self.path_segments: Dict[str, Set[str]] = defaultdict(set)

        # Performance tracking
        self.last_scan_time = 0.0
        self.scan_duration = 0.0
        self.is_scanning = False

        # File extension filtering
        self.common_extensions = {
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
            ".rb",
            ".go",
            ".rs",
            ".php",
            ".swift",
            ".kt",
            ".scala",
            ".clj",
            ".hs",
            ".md",
            ".txt",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".cfg",
            ".html",
            ".css",
            ".scss",
            ".sass",
            ".less",
            ".sh",
            ".bat",
            ".ps1",
            ".dockerfile",
            ".makefile",
        }

        # Ignore patterns
        self.ignore_dirs = {
            ".git",
            ".svn",
            ".hg",
            ".bzr",
            "__pycache__",
            ".mypy_cache",
            ".pytest_cache",
            "node_modules",
            ".venv",
            "venv",
            "env",
            ".next",
            ".nuxt",
            "dist",
            "build",
            "target",
            ".vscode",
            ".idea",
            ".vs",
        }

        self.ignore_files = {
            ".gitignore",
            ".gitmodules",
            ".gitattributes",
            ".DS_Store",
            "Thumbs.db",
            ".directory",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            "__pycache__",
        }

    async def initialize(self) -> None:
        """Initialize the index with initial scan."""
        await self._full_scan()

    async def _full_scan(self) -> None:
        """Perform full filesystem scan."""
        if self.is_scanning:
            return

        self.is_scanning = True
        start_time = time.time()

        try:
            # Clear existing indexes
            self.files.clear()
            self.directories.clear()
            self.path_segments.clear()

            # Scan filesystem
            await self._scan_directory(self.root_path, 0)

            # Build path segment index for fast lookups
            self._build_segment_index()

        finally:
            self.scan_duration = time.time() - start_time
            self.last_scan_time = time.time()
            self.is_scanning = False

    async def _scan_directory(self, dir_path: Path, depth: int) -> None:
        """Recursively scan directory structure."""
        if depth > self.max_depth or len(self.files) > self.max_files:
            return

        try:
            rel_path = str(dir_path.relative_to(self.root_path))
            if rel_path == ".":
                rel_path = ""

            children = []

            # Process directory entries
            for entry in dir_path.iterdir():
                # Skip hidden and ignored items
                if entry.name.startswith(".") and entry.name not in {
                    ".env",
                    ".gitignore",
                }:
                    continue

                if entry.is_dir():
                    if entry.name in self.ignore_dirs:
                        continue

                    child_rel_path = str(entry.relative_to(self.root_path))
                    children.append(child_rel_path + "/")

                    # Add to directories index
                    self.directories[child_rel_path] = DirectoryEntry(
                        path=child_rel_path, children=[], mtime=entry.stat().st_mtime
                    )

                    # Recursively scan subdirectory
                    await self._scan_directory(entry, depth + 1)

                elif entry.is_file():
                    if self._should_ignore_file(entry):
                        continue

                    child_rel_path = str(entry.relative_to(self.root_path))
                    children.append(child_rel_path)

                    # Add to files index
                    stat = entry.stat()
                    self.files[child_rel_path] = FileEntry(
                        path=child_rel_path,
                        size=stat.st_size,
                        mtime=stat.st_mtime,
                        is_dir=False,
                    )

            # Update directory children
            if rel_path in self.directories:
                self.directories[rel_path].children = children
            elif rel_path == "":
                # Root directory
                self.directories[""] = DirectoryEntry(
                    path="", children=children, mtime=dir_path.stat().st_mtime
                )

        except (PermissionError, OSError):
            # Skip directories we can't read
            pass

    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        # Check extension
        if file_path.suffix.lower() not in self.common_extensions and file_path.suffix:
            return True

        # Check ignore patterns
        if file_path.name in self.ignore_files:
            return True

        # Check size (skip very large files)
        try:
            if file_path.stat().st_size > 1024 * 1024:  # 1MB limit
                return True
        except OSError:
            return True

        return False

    def _build_segment_index(self) -> None:
        """Build path segment index for fast fuzzy matching."""
        for path in list(self.files.keys()) + list(self.directories.keys()):
            if not path:
                continue

            # Add full path
            self.path_segments[path.lower()].add(path)

            # Add path segments
            parts = path.split("/")
            for i in range(len(parts)):
                segment = "/".join(parts[: i + 1])
                if segment:
                    self.path_segments[segment.lower()].add(path)

                # Add just the component name
                component = parts[i]
                if component:
                    self.path_segments[component.lower()].add(path)

    def get_fuzzy_matches(self, query: str, limit: int = 10) -> List[Tuple[str, float]]:
        """Get fuzzy matches for a query with relevance scoring."""
        if not query:
            return []

        query_lower = query.lower()
        matches = []

        # If the query is a directory, add it as a high-priority match
        dir_path = query.rstrip("/")
        if self.is_directory(dir_path):
            matches.append((dir_path + "/", 2.0))  # High score to prioritize

        # Direct segment matches (highest priority)
        if query_lower in self.path_segments:
            for path in self.path_segments[query_lower]:
                matches.append((path, 1.0))

        # Prefix matches
        for segment, paths in self.path_segments.items():
            if segment.startswith(query_lower) and segment != query_lower:
                for path in paths:
                    score = len(query_lower) / len(segment)
                    matches.append((path, score * 0.9))

        # Substring matches (lower priority)
        for segment, paths in self.path_segments.items():
            if query_lower in segment and not segment.startswith(query_lower):
                for path in paths:
                    score = len(query_lower) / len(segment)
                    matches.append((path, score * 0.7))

        # Remove duplicates and sort by score
        seen = set()
        unique_matches = []
        for path, score in matches:
            if path not in seen:
                seen.add(path)
                unique_matches.append((path, score))

        # Sort by score (descending), then by path length (ascending)
        unique_matches.sort(key=lambda x: (-x[1], len(x[0])))

        return unique_matches[:limit]

    def get_directory_contents(self, dir_path: str) -> List[str]:
        """Get contents of a specific directory."""
        if dir_path.endswith("/"):
            dir_path = dir_path[:-1]

        if dir_path in self.directories:
            return self.directories[dir_path].children.copy()
        return []

    def get_files_in_directory(self, dir_path: str) -> List[str]:
        """Get only files (not directories) in a specific directory."""
        contents = self.get_directory_contents(dir_path)
        return [item for item in contents if not item.endswith("/")]

    def get_subdirectories(self, dir_path: str) -> List[str]:
        """Get only subdirectories in a specific directory."""
        contents = self.get_directory_contents(dir_path)
        return [item for item in contents if item.endswith("/")]

    def path_exists(self, path: str) -> bool:
        """Check if a path exists in the index."""
        return path in self.files or path in self.directories

    def is_directory(self, path: str) -> bool:
        """Check if a path is a directory."""
        return path in self.directories

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            "files": len(self.files),
            "directories": len(self.directories),
            "last_scan": self.last_scan_time,
            "scan_duration": self.scan_duration,
            "is_scanning": self.is_scanning,
            "path_segments": sum(len(paths) for paths in self.path_segments.values()),
        }

    async def refresh_if_stale(self, max_age: float = 60.0) -> bool:
        """Refresh index if it's older than max_age seconds."""
        if time.time() - self.last_scan_time > max_age:
            await self._full_scan()
            return True
        return False


# Global instance for the application
_global_index: Optional[FileSystemIndex] = None


async def get_file_index() -> FileSystemIndex:
    """Get or create global file index instance."""
    global _global_index
    if _global_index is None:
        _global_index = FileSystemIndex()
        await _global_index.initialize()
    return _global_index


def reset_file_index() -> None:
    """Reset global file index (for testing)."""
    global _global_index
    _global_index = None
