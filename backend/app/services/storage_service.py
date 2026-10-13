"""Local file storage abstraction for raw PDF files with strict path-traversal prevention."""

import os
import shutil
from pathlib import Path
from app.core.config import settings
from app.core.errors import ValidationException


class StorageService:
    def __init__(self, base_dir: Path = settings.STORAGE_DIR):
        self.base_dir = base_dir.resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_workspace_dir(self, workspace_id: str) -> Path:
        # Sanitize workspace_id against directory traversal
        clean_id = os.path.basename(workspace_id)
        ws_dir = (self.base_dir / "workspaces" / clean_id).resolve()
        if not ws_dir.is_relative_to(self.base_dir):
            raise ValidationException("Invalid storage directory path.")
        ws_dir.mkdir(parents=True, exist_ok=True)
        return ws_dir

    def _safe_file_path(self, workspace_id: str, stored_filename: str) -> Path:
        clean_filename = os.path.basename(stored_filename)
        ws_dir = self._get_workspace_dir(workspace_id)
        file_path = (ws_dir / clean_filename).resolve()
        if not file_path.is_relative_to(ws_dir):
            raise ValidationException("Detected illegal path traversal attempt.")
        return file_path

    def save_file(self, workspace_id: str, stored_filename: str, content: bytes) -> Path:
        target_path = self._safe_file_path(workspace_id, stored_filename)
        with open(target_path, "wb") as f:
            f.write(content)
        return target_path

    def get_file_path(self, workspace_id: str, stored_filename: str) -> Path:
        return self._safe_file_path(workspace_id, stored_filename)

    def delete_file(self, workspace_id: str, stored_filename: str) -> bool:
        file_path = self._safe_file_path(workspace_id, stored_filename)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def delete_workspace_files(self, workspace_id: str) -> bool:
        ws_dir = self._get_workspace_dir(workspace_id)
        if ws_dir.exists():
            shutil.rmtree(ws_dir)
            return True
        return False

    def delete_workspace_dir(self, workspace_id: str) -> bool:
        return self.delete_workspace_files(workspace_id)


storage_service = StorageService()
