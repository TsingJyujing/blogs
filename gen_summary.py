#!/usr/bin/env python3
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set


def get_h1_title(path: Path) -> str:
    """Extract the first H1 title from a markdown file, or raise ValueError."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if not (stripped := line.strip()):
            continue
        if match := re.match(r"^#\s+(.*)", stripped):
            return match.group(1).strip()
        raise ValueError(f"Missing H1 title in: {path}")
    raise ValueError(f"File is empty: {path}")


def collect_structure(
    directory: Path, root: Path, ignore: Set[str], depth: int = 0
) -> List[Dict[str, Any]]:
    """Recursively collect directory structure and metadata."""
    nodes = []
    for item in directory.iterdir():
        if (
            item.name in ignore
            or item.name.startswith(".")
            or item.name == "SUMMARY.md"
        ):
            continue

        if item.is_dir():
            readme_path = item / "README.md"
            if readme_path.exists():
                nodes.append(
                    {
                        "path": str(readme_path),
                        "title": get_h1_title(readme_path),
                        "children": collect_structure(item, root, ignore, depth + 1),
                        "mtime": readme_path.stat().st_mtime,
                    }
                )
        elif item.suffix == ".md" and item.name.lower() != "readme.md":
            nodes.append(
                {
                    "path": str(item),
                    "title": get_h1_title(item),
                    "children": None,
                    "mtime": item.stat().st_mtime,
                }
            )

    if depth == 0:
        return sorted(nodes, key=lambda node: node["path"])
    else:
        return sorted(nodes, key=lambda node: node["mtime"], reverse=True)


def generate_markdown_lines(
    data: List[Dict[str, Any]], root: Path, depth: int = 0
) -> Iterable[str]:
    """Convert the collected data structure into Markdown list lines."""
    for node in data:
        title = node["title"]
        relative_path = Path(node["path"]).relative_to(root)
        indent = "  " * depth
        yield f"{indent}* [{title}]({relative_path})"
        if node["children"]:
            yield from generate_markdown_lines(node["children"], root, depth + 1)


if __name__ == "__main__":
    root_path = Path.cwd()
    ignore_set = {"img", "node_modules", "gen_summary.py", ".git", ".vscode"}
    with (root_path / "SUMMARY.md").open("w", encoding="utf-8") as fp:
        fp.write("# Table of contents\n\n")
        if (root_path / "README.md").exists():
            root_title = get_h1_title(root_path / "README.md")
            fp.write(f"* [{root_title}](README.md)\n")
        fp.writelines(
            f"{s}\n"
            for s in generate_markdown_lines(
                collect_structure(root_path, root_path, ignore_set), root_path
            )
        )
