"""Pure utility functions for file operations and path resolution."""
import difflib
import os
from pathlib import Path
from typing import List, Optional


def resolve_file_path(file_ref: str) -> Optional[str]:
    """Resolve a file reference to an actual file path.

    Args:
        file_ref: File reference that could be exact path, filename, or partial path

    Returns:
        Resolved file path if found, None otherwise
    """
    # Try exact match first
    if os.path.exists(file_ref):
        return file_ref

    # Try with common extensions
    common_extensions = [
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
    ]
    for ext in common_extensions:
        if not file_ref.endswith(ext):
            candidate = f"{file_ref}{ext}"
            if os.path.exists(candidate):
                return candidate

    # Try fuzzy matching in current directory and subdirectories
    project_items = _get_project_items()

    # Find best matches using fuzzy matching
    item_names = [os.path.basename(f.rstrip("/")) for f in project_items]
    matches = difflib.get_close_matches(file_ref, item_names, n=1, cutoff=0.6)

    if matches:
        # Find the full path of the matched item
        for full_path in project_items:
            if os.path.basename(full_path.rstrip("/")) == matches[0]:
                return full_path

    # Try matching against file stems (without extension)
    file_stems = [Path(f.rstrip("/")).stem for f in project_items]
    stem_matches = difflib.get_close_matches(file_ref, file_stems, n=1, cutoff=0.6)

    if stem_matches:
        for full_path in project_items:
            if Path(full_path.rstrip("/")).stem == stem_matches[0]:
                return full_path

    return None


def get_file_suggestions(file_ref: str) -> List[str]:
    """Get file and directory suggestions for a failed file reference.

    Args:
        file_ref: File reference that wasn't found

    Returns:
        List of suggested file/directory paths
    """
    try:
        # Check if file_ref looks like a complete directory path
        if file_ref.endswith("/") and os.path.isdir(file_ref.rstrip("/")):
            # Show contents of this specific directory
            return get_directory_contents(file_ref.rstrip("/"))

        # Check if file_ref is a valid directory without trailing slash
        if os.path.isdir(file_ref):
            return get_directory_contents(file_ref)

        project_items = _get_project_items()
        project_dirs = _get_project_directories()

        # Get close matches for files and directories separately
        item_names = [os.path.basename(f.rstrip("/")) for f in project_items]
        dir_names = [os.path.basename(d.rstrip("/")) for d in project_dirs]

        # Match against file names and directory names
        file_matches = difflib.get_close_matches(file_ref, item_names, n=3, cutoff=0.4)
        dir_matches = difflib.get_close_matches(file_ref, dir_names, n=3, cutoff=0.4)

        # Also match against full paths for deeper navigation
        all_paths = project_items + project_dirs
        path_matches = difflib.get_close_matches(file_ref, all_paths, n=3, cutoff=0.3)

        # Combine suggestions, prioritizing exact matches and shorter paths
        suggestions = []

        # Add directory matches first (for easier navigation)
        for match in dir_matches:
            matching_dirs = [
                d for d in project_dirs if os.path.basename(d.rstrip("/")) == match
            ]
            suggestions.extend(matching_dirs)

        # Add file matches
        for match in file_matches:
            matching_files = [f for f in project_items if os.path.basename(f) == match]
            suggestions.extend(matching_files)

        # Add path matches (for partial path typing like "src/ai")
        suggestions.extend([p for p in path_matches if p not in suggestions])

        # Deduplicate and return top suggestions
        seen = set()
        unique_suggestions = []
        for item in suggestions:
            if item not in seen:
                seen.add(item)
                unique_suggestions.append(item)

        return unique_suggestions[:8]  # Return top 8 suggestions

    except Exception:
        return []


def get_directory_contents(dir_path: str) -> List[str]:
    """Get contents of a specific directory for suggestions.

    Args:
        dir_path: Directory path to list

    Returns:
        List of files and directories in the given directory
    """
    try:
        suggestions = []
        common_extensions = {
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".rb",
            ".go",
            ".rs",
            ".md",
            ".txt",
            ".json",
            ".yaml",
            ".yml",
        }

        # Get immediate children of this directory
        if os.path.exists(dir_path):
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                relative_item_path = os.path.relpath(item_path, ".")

                if (
                    os.path.isdir(item_path)
                    and not item.startswith(".")
                    and item not in ["__pycache__", "node_modules", ".git"]
                ):
                    # Add subdirectory with trailing slash
                    suggestions.append(relative_item_path + "/")
                elif os.path.isfile(item_path) and not item.startswith("."):
                    # Add files with common extensions or any file in root
                    if Path(item).suffix in common_extensions or dir_path == ".":
                        suggestions.append(relative_item_path)

        # Sort: directories first, then files
        dirs = sorted([s for s in suggestions if s.endswith("/")])
        files = sorted([s for s in suggestions if not s.endswith("/")])

        return dirs + files

    except Exception:
        return []


def get_all_file_suggestions() -> List[str]:
    """Get all available files and directories for initial @ suggestions.

    Returns:
        List of all available files and directories
    """
    try:
        project_items = []
        project_dirs = []
        common_extensions = {
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".rb",
            ".go",
            ".rs",
            ".md",
            ".txt",
            ".json",
            ".yaml",
            ".yml",
        }

        for root, dirs, files in os.walk("."):
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d
                not in [
                    "__pycache__",
                    "node_modules",
                    ".git",
                    ".mypy_cache",
                    ".pytest_cache",
                ]
            ]

            # Calculate relative path from current directory
            if root == ".":
                prefix = ""
            else:
                prefix = root[2:] + "/"  # Remove './' and add trailing slash

            # Add directories (prioritize shorter paths)
            if root == "." or root.count("/") <= 2:  # Current dir + 2 levels deep max
                for dir_name in dirs:
                    full_dir_path = prefix + dir_name + "/"
                    project_dirs.append(full_dir_path)

            # Add files with common extensions (limit depth)
            if root.count("/") <= 2:  # Current dir + 2 levels deep max
                for file in files:
                    if Path(file).suffix in common_extensions or (
                        not file.startswith(".") and root == "."
                    ):
                        full_file_path = prefix + file
                        project_items.append(full_file_path)

        # Combine directories first (for easier navigation), then files
        all_suggestions = sorted(project_dirs) + sorted(project_items)
        return all_suggestions[:12]  # Return top 12 suggestions

    except Exception:
        return []


def format_file_content(file_path: str, content: str, detail_mode: bool = False) -> str:
    """Format file content based on detail mode.

    Args:
        file_path: Path to the file
        content: File content
        detail_mode: If True, show full content; if False, show summary

    Returns:
        Formatted file content string
    """
    if not detail_mode:
        # Summary mode - show file info and first 10 lines
        lines = content.split("\n")
        total_lines = len(lines)
        preview_lines = lines[:10]

        summary = f"**File: {file_path}** ({total_lines} lines)\n"
        summary += "```\n" + "\n".join(preview_lines)
        if total_lines > 10:
            summary += (
                f"\n... ({total_lines - 10} more lines) - Use Ctrl+R for full content"
            )
        summary += "\n```"
        return summary
    else:
        # Detailed mode - show full content
        return f"**File: {file_path}** (Full Content)\n```\n{content}\n```"


def _get_project_items() -> List[str]:
    """Get all project files with filtering and depth limits.

    Returns:
        List of project file paths
    """
    project_items = []
    try:
        for root, dirs, files in os.walk("."):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d
                not in [
                    "__pycache__",
                    "node_modules",
                    ".git",
                    ".mypy_cache",
                    ".pytest_cache",
                ]
            ]

            # Calculate relative path
            if root == ".":
                prefix = ""
            else:
                prefix = root[2:] + "/"  # Remove './' prefix

            # Add directories (limit depth)
            if root.count("/") <= 1:  # Current dir + 1 level deep
                for dir_name in dirs:
                    full_dir_path = prefix + dir_name + "/"
                    project_items.append(full_dir_path)

            # Add files (limit depth)
            if root.count("/") <= 2:  # Current dir + 2 levels deep
                for file in files:
                    if not file.startswith(".") and not file.endswith(".pyc"):
                        full_file_path = prefix + file
                        project_items.append(full_file_path)
    except Exception:
        pass

    return project_items


def _get_project_directories() -> List[str]:
    """Get all project directories with filtering and depth limits.

    Returns:
        List of project directory paths
    """
    project_dirs = []
    try:
        for root, dirs, files in os.walk("."):
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d not in ["__pycache__", "node_modules", ".git"]
            ]

            # Add directories with trailing slash
            for dir_name in dirs:
                rel_path = os.path.relpath(os.path.join(root, dir_name), ".") + "/"
                project_dirs.append(rel_path)
    except Exception:
        pass

    return project_dirs
