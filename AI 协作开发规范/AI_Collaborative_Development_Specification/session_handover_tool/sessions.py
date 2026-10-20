"""Atomic config/receipts and a bounded per-project registration lock."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

from .config import absolute, identifier
from .errors import ToolError


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


class Store:
    def __init__(self, config):
        # Both ID and resolved root isolate projects sharing the same runtime base.
        root_hash = hashlib.sha256(os.path.normcase(str(absolute(config["project_root"]))).encode()).hexdigest()[:16]
        self.root = absolute(config["runtime_dir"]) / (config["project_id"] + "-" + root_hash)

    def request_path(self, request_id):
        return self.root / "requests" / (identifier(request_id, "request_id") + ".json")

    def claim_config(self, path):
        owner = self.root / "config-source.json"
        if owner.exists() and Path(read(owner)["config"]).resolve() != Path(path).resolve():
            raise ToolError("config_conflict", "Do not create a second config source for the same project runtime")
        if not owner.exists():save(owner, {"config": str(Path(path).resolve())})

    def task_path(self, milestone, task_id):
        return self.root / "tasks" / identifier(milestone, "milestone") / (identifier(task_id, "task_id") + ".json")

    def pending_role(self, milestone, role):
        for path in (self.root / "requests").glob("*.json"):
            row = read(path)
            if (row.get("milestone"), row.get("role")) == (milestone, role) and row.get("action") in ("create", "switch") and row.get("status") in ("attempting", "unknown"):
                return row
        return None

    @contextmanager
    def lock(self, timeout=70):
        self.root.mkdir(parents=True, exist_ok=True)
        with (self.root / "registration.lock").open("a+b") as stream:
            stream.seek(0, os.SEEK_END)
            if stream.tell() == 0:
                stream.write(b"0"); stream.flush()
            deadline = time.monotonic() + timeout
            while True:
                try:
                    stream.seek(0)
                    if os.name == "nt":
                        import msvcrt
                        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise ToolError("busy", "Project registration lock is busy")
                    time.sleep(.05)
            try:
                yield
            finally:
                stream.seek(0)
                if os.name == "nt":
                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
