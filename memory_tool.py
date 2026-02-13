import os
import shutil
import functools
from pathlib import Path
from anthropic.lib.tools import BetaAbstractMemoryTool
from anthropic.types.beta import (
    BetaMemoryTool20250818ViewCommand,
    BetaMemoryTool20250818CreateCommand,
    BetaMemoryTool20250818DeleteCommand,
    BetaMemoryTool20250818StrReplaceCommand,
    BetaMemoryTool20250818InsertCommand,
    BetaMemoryTool20250818RenameCommand,
)

MEMORIES_DIR = Path(__file__).parent / "memories"


def _command_data(command):
    """Extract all public fields from a memory tool command."""
    return {k: v for k, v in vars(command).items() if not k.startswith('_')}


def _logged(func):
    @functools.wraps(func)
    def wrapper(self, command):
        name = func.__name__
        data = _command_data(command)
        self.log('info', f'memory_{name}', f"Memory: {name}", data)
        try:
            result = func(self, command)
            self.log('info', f'memory_{name}_done', f"Memory: {name} done", {**data, 'result_preview': str(result)[:200]})
            return result
        except Exception as e:
            self.log('error', f'memory_{name}_error', f"Memory: {name} failed", {**data, 'error': str(e), 'type': type(e).__name__})
            raise
    return wrapper


class LocalMemoryTool(BetaAbstractMemoryTool):
    def __init__(self, log_func=None):
        super().__init__()
        MEMORIES_DIR.mkdir(exist_ok=True)
        self.log = log_func or (lambda *a, **kw: None)

    def _resolve(self, virtual_path: str) -> Path:
        """Resolve a /memories/... virtual path to a real filesystem path, preventing traversal."""
        # Strip leading /memories or /memories/ prefix
        rel = virtual_path.strip("/")
        if rel.startswith("memories"):
            rel = rel[len("memories"):].lstrip("/")
        resolved = (MEMORIES_DIR / rel).resolve()
        if not str(resolved).startswith(str(MEMORIES_DIR.resolve())):
            raise ValueError(f"Path traversal denied: {virtual_path}")
        return resolved

    @_logged
    def view(self, command: BetaMemoryTool20250818ViewCommand) -> str:
        path = self._resolve(command.path)
        if path.is_dir():
            return self._list_dir(path, command.path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {command.path}")
        lines = path.read_text().splitlines(keepends=True)
        if command.view_range:
            start, end = command.view_range[0], command.view_range[1]
            lines = lines[start - 1:end]
            start_num = start
        else:
            start_num = 1
        numbered = "".join(f"{i}\t{line}" for i, line in enumerate(lines, start=start_num))
        return numbered or "(empty file)"

    def _list_dir(self, real_path: Path, virtual_path: str) -> str:
        entries = []
        for item in sorted(real_path.iterdir()):
            rel = item.relative_to(MEMORIES_DIR)
            vpath = f"/memories/{rel}"
            if item.is_dir():
                entries.append(f"  {vpath}/")
                for sub in sorted(item.iterdir()):
                    sub_rel = sub.relative_to(MEMORIES_DIR)
                    sub_vpath = f"/memories/{sub_rel}"
                    if sub.is_dir():
                        entries.append(f"    {sub_vpath}/")
                    else:
                        size = sub.stat().st_size
                        entries.append(f"    {sub_vpath} ({size} bytes)")
            else:
                size = item.stat().st_size
                entries.append(f"  {vpath} ({size} bytes)")
        if not entries:
            return f"{virtual_path}: (empty directory)"
        return f"{virtual_path}:\n" + "\n".join(entries)

    @_logged
    def create(self, command: BetaMemoryTool20250818CreateCommand) -> str:
        path = self._resolve(command.path)
        if path.exists():
            raise FileExistsError(f"File already exists: {command.path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(command.file_text)
        return f"Created {command.path}"

    @_logged
    def str_replace(self, command: BetaMemoryTool20250818StrReplaceCommand) -> str:
        path = self._resolve(command.path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {command.path}")
        content = path.read_text()
        count = content.count(command.old_str)
        if count == 0:
            raise ValueError(f"old_str not found in {command.path}")
        if count > 1:
            raise ValueError(f"old_str found {count} times in {command.path}, must be unique")
        path.write_text(content.replace(command.old_str, command.new_str, 1))
        return f"Replaced in {command.path}"

    @_logged
    def insert(self, command: BetaMemoryTool20250818InsertCommand) -> str:
        path = self._resolve(command.path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {command.path}")
        lines = path.read_text().splitlines(keepends=True)
        insert_pos = command.insert_line
        # Ensure the inserted text ends with a newline
        text = command.insert_text if command.insert_text.endswith("\n") else command.insert_text + "\n"
        lines.insert(insert_pos, text)
        path.write_text("".join(lines))
        return f"Inserted at line {insert_pos} in {command.path}"

    @_logged
    def delete(self, command: BetaMemoryTool20250818DeleteCommand) -> str:
        path = self._resolve(command.path)
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {command.path}")
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        return f"Deleted {command.path}"

    @_logged
    def rename(self, command: BetaMemoryTool20250818RenameCommand) -> str:
        old = self._resolve(command.old_path)
        new = self._resolve(command.new_path)
        if not old.exists():
            raise FileNotFoundError(f"Path not found: {command.old_path}")
        if new.exists():
            raise FileExistsError(f"Destination already exists: {command.new_path}")
        new.parent.mkdir(parents=True, exist_ok=True)
        old.rename(new)
        return f"Renamed {command.old_path} -> {command.new_path}"
