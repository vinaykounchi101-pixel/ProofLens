"""Local file storage abstraction for raw PDF files."""

import os
import shutil
from pathlib import Path
from app.core.config import settings


class StorageService:
    def __init__(self, base_dir: Path = settings.STORAGE_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_workspace_dir(self, workspace_id: str) -> Path:
        ws_dir = self.base_dir / "workspaces" / workspace_id
        ws_dir.mkdir(parents=True, exist_ok=True)
        return ws_dir

    def save_file(self, workspace_id: str, stored_filename: str, content: bytes) -> Path:
        ws_dir = self._get_workspace_dir(workspace_id)
        target_path = ws_dir / stored_filename
        with open(target_path, "wb") as f:
            f.write(content)
        return target_path

    def get_file_path(self, workspace_id: str, stored_filename: str) -> Path:
        return self._get_workspace_dir(workspace_id) / stored_filename

    def delete_file(self, workspace_id: str, stored_filename: str) -> bool:
        file_path = self.get_file_path(workspace_id, stored_filename)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def delete_workspace_files(self, workspace_id: str) -> bool:
        ws_dir = self.base_dir / "workspaces" / workspace_id
        if ws_dir.exists():
            shutil.rmtree(ws_dir)
            return True
        return False


storage_service = StorageService()
