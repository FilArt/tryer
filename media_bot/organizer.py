import json
import shutil
from pathlib import Path


VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".mov", ".m4v", ".wmv"}
JUNK_PARTS = {"sample", "trailer"}


class Organizer:
    def __init__(self, planner):
        self.planner = planner

    def scan(self, root: str) -> list[str]:
        base = Path(root)
        files = []
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
                name = path.name.lower()
                if not any(part in name for part in JUNK_PARTS):
                    files.append(str(path.relative_to(base)))
        return files

    def make_plan(self, torrent_name: str, root: str) -> dict:
        return self.planner.plan(torrent_name, self.scan(root))

    def apply(self, root: str, plan: dict) -> list[str]:
        base = Path(root)
        moved = []
        for item in plan.get("items", []):
            source = base / item["source"]
            target = Path(item["target"])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
            moved.append(str(target))
        return moved

    def summary(self, plan: dict, moved: list[str] | None = None) -> str:
        lines = [
            f"Тип: {plan.get('content_type', 'unknown')}",
            f"Название: {plan.get('title', 'unknown')}",
            f"Уверенность: {plan.get('confidence', 0)}",
            f"Файлов: {len(plan.get('items', []))}",
        ]
        if moved is not None:
            lines.append("Перемещено:")
            lines.extend(moved)
        else:
            lines.append(json.dumps(plan, ensure_ascii=False, indent=2))
        return "\n".join(lines)
