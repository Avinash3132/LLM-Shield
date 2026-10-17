"""Mock File Vault Sandbox.

Enforces strict path normalization and path traversal prevention.
Restricted exclusively to harmless synthetic files within the designated sandbox vault.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional


class FileVaultSandbox:
    """Isolated file vault sandbox that strictly forbids path traversal."""

    def __init__(self, root_dir: Path | str):
        self.root_dir = Path(root_dir).resolve()
        if not self.root_dir.exists():
            self.root_dir.mkdir(parents=True, exist_ok=True)

    def _normalize_path(self, virtual_path: str) -> Path:
        """Strip virtual URI schemes (e.g., vault://) and resolve against root_dir."""
        cleaned = virtual_path.strip()
        if cleaned.startswith("vault://"):
            cleaned = cleaned[len("vault://") :]
        elif cleaned.startswith("vault:/"):
            cleaned = cleaned[len("vault:/") :]

        # Strip any leading slashes or backslashes
        cleaned = cleaned.lstrip("/\\")

        # Resolve full path
        target = (self.root_dir / cleaned).resolve()

        # Strict sandbox isolation: verify target is inside root_dir
        try:
            target.relative_to(self.root_dir)
        except ValueError:
            raise PermissionError(
                f"Path traversal blocked: target path '{virtual_path}' resolves outside sandbox."
            )

        return target

    def read_file(self, virtual_path: str) -> Dict[str, Any]:
        """Read a file within the sandbox file vault."""
        try:
            target = self._normalize_path(virtual_path)
            if not target.exists():
                return {
                    "success": False,
                    "error": f"File not found: '{virtual_path}'",
                    "path": virtual_path,
                }
            if not target.is_file():
                return {
                    "success": False,
                    "error": f"Path is a directory, not a file: '{virtual_path}'",
                    "path": virtual_path,
                }

            content = target.read_text(encoding="utf-8")
            return {
                "success": True,
                "path": virtual_path,
                "content": content,
                "bytes": len(content.encode("utf-8")),
            }
        except PermissionError as e:
            return {
                "success": False,
                "error": str(e),
                "path": virtual_path,
                "security_violation": "PATH_TRAVERSAL_DETECTED",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Read error: {str(e)}",
                "path": virtual_path,
            }

    def list_files(self, virtual_dir: str = "") -> Dict[str, Any]:
        """List files in the vault or a subdirectory thereof."""
        try:
            target_dir = self._normalize_path(virtual_dir)
            if not target_dir.exists() or not target_dir.is_dir():
                return {
                    "success": False,
                    "error": f"Directory not found: '{virtual_dir}'",
                    "files": [],
                }

            entries = []
            for item in target_dir.rglob("*"):
                if item.is_file():
                    rel = item.relative_to(self.root_dir).as_posix()
                    entries.append(
                        {
                            "virtual_path": f"vault://{rel}",
                            "relative_path": rel,
                            "bytes": item.stat().st_size,
                        }
                    )

            return {
                "success": True,
                "directory": virtual_dir,
                "files": entries,
                "count": len(entries),
            }
        except PermissionError as e:
            return {
                "success": False,
                "error": str(e),
                "security_violation": "PATH_TRAVERSAL_DETECTED",
            }
