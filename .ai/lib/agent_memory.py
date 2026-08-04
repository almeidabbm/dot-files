#!/usr/bin/env python3
"""Deterministic local state management for the shared agent workflow."""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Iterable, Sequence
from urllib.parse import urlparse


SCHEMA_VERSION = 1
EXPECTED_TASK_FILES = ("spec.md", "plan.md", "notes.md", "review.md")
SKIP_DISCOVERY_DIRS = {".git", ".worktrees", "node_modules", "vendor"}
SLUG_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")


class AgentMemoryError(RuntimeError):
    """A safe, user-facing agent-memory failure."""


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_tree(path: Path) -> str:
    digest = hashlib.sha256()
    if not path.exists():
        return digest.hexdigest()
    for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
        relative = item.relative_to(path).as_posix()
        if relative == ".DS_Store":
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def git(path: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(path), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def git_root(path: Path) -> Path | None:
    value = git(path, "rev-parse", "--show-toplevel")
    return Path(value).resolve() if value else None


def normalize_remote(remote: str) -> str:
    value = remote.strip()
    scp_match = re.match(r"^(?:[^@/]+@)?([^:/]+):(.+)$", value)
    if scp_match and "://" not in value:
        host, remote_path = scp_match.groups()
    else:
        parsed = urlparse(value)
        if parsed.scheme in {"http", "https", "ssh", "git"} and parsed.hostname:
            host = parsed.hostname
            remote_path = parsed.path
        else:
            raise AgentMemoryError("repository remote is not a supported network URL")

    host = host.lower().strip()
    remote_path = remote_path.strip("/")
    if remote_path.endswith(".git"):
        remote_path = remote_path[:-4]
    parts = [part for part in remote_path.split("/") if part and part not in {".", ".."}]
    if not host or not parts:
        raise AgentMemoryError("repository remote does not contain a safe identity")
    return "/".join([host, *parts])


def repository_id(path: Path) -> str:
    checkout = git_root(path) or path.resolve()
    remote = git(checkout, "remote", "get-url", "origin")
    if remote:
        try:
            return normalize_remote(remote)
        except AgentMemoryError:
            pass
    label = re.sub(r"[^a-zA-Z0-9._-]+", "-", checkout.name).strip("-") or "repo"
    suffix = sha256_bytes(str(checkout).encode("utf-8"))[:12]
    return f"local/{label}-{suffix}"


def default_memory_root(environ: dict[str, str] | None = None) -> Path:
    env = environ if environ is not None else os.environ
    configured = env.get("AGENT_LOCAL_MEMORY_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    data_home = env.get("XDG_DATA_HOME")
    base = Path(data_home).expanduser() if data_home else Path.home() / ".local" / "share"
    return (base / "agent-memory").resolve()


def validate_memory_root(
    root: Path,
    *,
    repository: Path | None = None,
    allow_repository_local: bool = False,
) -> Path:
    resolved = root.expanduser().resolve()
    home = Path.home().resolve()
    if resolved in {Path("/"), home}:
        raise AgentMemoryError("memory root must not be the filesystem or home root")
    if ".git" in resolved.parts:
        raise AgentMemoryError("memory root must not be inside Git metadata")
    if repository and not allow_repository_local:
        repo = (git_root(repository) or repository).resolve()
        if is_relative_to(resolved, repo):
            raise AgentMemoryError("central memory root must be outside the repository")
    return resolved


def resolve_memory_root(
    *,
    repository: Path | None = None,
    legacy_fallback: bool = False,
    environ: dict[str, str] | None = None,
) -> Path:
    env = environ if environ is not None else os.environ
    if legacy_fallback and not env.get("AGENT_LOCAL_MEMORY_PATH") and repository:
        repo = git_root(repository) or repository.resolve()
        legacy = repo / ".local"
        if legacy.exists():
            return validate_memory_root(
                legacy, repository=repo, allow_repository_local=True
            )
    return validate_memory_root(
        default_memory_root(env), repository=repository, allow_repository_local=False
    )


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AgentMemoryError(f"invalid JSON state file: {path}") from exc


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def parse_frontmatter(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    result: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line or line.startswith((" ", "\t")):
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def set_frontmatter(path: Path, updates: dict[str, str], remove: set[str] | None = None) -> None:
    remove = remove or set()
    original = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = original.splitlines()
    if not lines or lines[0].strip() != "---":
        header = ["---", *(f"{key}: {value}" for key, value in updates.items()), "---"]
        path.write_text("\n".join(header) + "\n\n" + original, encoding="utf-8")
        return

    end = next((index for index, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if end is None:
        raise AgentMemoryError(f"unterminated frontmatter: {path}")
    seen: set[str] = set()
    header: list[str] = ["---"]
    for line in lines[1:end]:
        if ":" not in line or line.startswith((" ", "\t")):
            header.append(line)
            continue
        key = line.split(":", 1)[0].strip()
        if key in remove:
            continue
        if key in updates:
            header.append(f"{key}: {updates[key]}")
            seen.add(key)
        else:
            header.append(line)
    for key, value in updates.items():
        if key not in seen:
            header.append(f"{key}: {value}")
    header.append("---")
    new_lines = [*header, *lines[end + 1 :]]
    path.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")


def initialize_root(root: Path) -> None:
    for relative in (
        "tasks/active",
        "tasks/archive",
        "repositories",
        "registry",
        "migrations",
        ".staging",
    ):
        (root / relative).mkdir(parents=True, exist_ok=True, mode=0o700)


def current_branch(path: Path) -> str:
    return git(path, "branch", "--show-current") or ""


def task_directories(root: Path, states: Sequence[str] = ("active", "archive")) -> list[Path]:
    tasks: list[Path] = []
    for state in states:
        state_root = root / "tasks" / state
        if state_root.exists():
            tasks.extend(sorted(item for item in state_root.iterdir() if item.is_dir()))
    return tasks


def task_manifest(task_dir: Path) -> dict[str, Any] | None:
    manifest_path = task_dir / "task.json"
    if not manifest_path.exists():
        return None
    value = read_json(manifest_path, {})
    return value if isinstance(value, dict) else None


def find_task(root: Path, reference: str, states: Sequence[str] = ("active", "archive")) -> Path:
    matches: list[Path] = []
    for task_dir in task_directories(root, states):
        manifest = task_manifest(task_dir) or {}
        if reference in {
            task_dir.name,
            str(manifest.get("id", "")),
            str(manifest.get("slug", "")),
        }:
            matches.append(task_dir)
    if not matches:
        raise AgentMemoryError(f"task not found: {reference}")
    if len(matches) > 1:
        raise AgentMemoryError(f"task reference is ambiguous: {reference}")
    return matches[0]


def load_bindings(root: Path) -> dict[str, Any]:
    value = read_json(
        root / "registry" / "bindings.json",
        {"schema_version": SCHEMA_VERSION, "bindings": []},
    )
    if not isinstance(value, dict) or not isinstance(value.get("bindings"), list):
        raise AgentMemoryError("bindings registry has an invalid shape")
    return value


def register_repository(root: Path, checkout: Path) -> str:
    repo_root = git_root(checkout) or checkout.resolve()
    repo_id = repository_id(repo_root)
    path = root / "registry" / "repositories.json"
    registry = read_json(
        path,
        {"schema_version": SCHEMA_VERSION, "repositories": []},
    )
    if not isinstance(registry, dict) or not isinstance(
        registry.get("repositories"), list
    ):
        raise AgentMemoryError("repository registry has an invalid shape")
    existing = next(
        (item for item in registry["repositories"] if item.get("id") == repo_id),
        None,
    )
    checkouts = set(existing.get("checkouts", []) if existing else [])
    checkouts.add(str(repo_root))
    entry = {
        "id": repo_id,
        "checkouts": sorted(checkouts),
        "updated_at": utc_now(),
    }
    registry["repositories"] = [
        item for item in registry["repositories"] if item.get("id") != repo_id
    ]
    registry["repositories"].append(entry)
    atomic_write_json(path, registry)
    return repo_id


def bind_task(root: Path, task_id: str, checkout: Path, branch: str | None = None) -> None:
    initialize_root(root)
    repo_root = git_root(checkout) or checkout.resolve()
    repo_id = register_repository(root, repo_root)
    selected_branch = current_branch(repo_root) if branch is None else branch
    registry = load_bindings(root)
    bindings = [
        entry
        for entry in registry["bindings"]
        if not (
            entry.get("repo_id") == repo_id
            and entry.get("checkout") == str(repo_root)
        )
    ]
    bindings.append(
        {
            "repo_id": repo_id,
            "checkout": str(repo_root),
            "branch": selected_branch,
            "task_id": task_id,
            "updated_at": utc_now(),
        }
    )
    registry["bindings"] = bindings
    atomic_write_json(root / "registry" / "bindings.json", registry)


def resolve_current_task(root: Path, checkout: Path, explicit: str | None = None) -> Path:
    if explicit:
        return find_task(root, explicit, ("active",))
    environment_task = os.environ.get("AGENT_TASK_ID")
    if environment_task:
        return find_task(root, environment_task, ("active",))

    repo_root = git_root(checkout) or checkout.resolve()
    repo_id = repository_id(repo_root)
    branch = current_branch(repo_root)
    registry = load_bindings(root)
    candidates = [
        entry
        for entry in registry["bindings"]
        if entry.get("repo_id") == repo_id and entry.get("checkout") == str(repo_root)
    ]
    exact = [entry for entry in candidates if entry.get("branch") == branch]
    selected = exact[-1:] or candidates[-1:]
    if selected:
        return find_task(root, str(selected[0]["task_id"]), ("active",))

    repo_matches: list[Path] = []
    for task_dir in task_directories(root, ("active",)):
        manifest = task_manifest(task_dir) or {}
        repositories = manifest.get("repositories", [])
        if any(item.get("id") == repo_id for item in repositories if isinstance(item, dict)):
            repo_matches.append(task_dir)
    if len(repo_matches) == 1:
        return repo_matches[0]
    if not repo_matches:
        raise AgentMemoryError("no active task is bound to this repository")
    raise AgentMemoryError("multiple active tasks match this repository; bind one explicitly")


def task_templates(
    *,
    task_id: str,
    slug: str,
    title: str,
    ticket: str,
    size: str,
    repositories: list[dict[str, str]],
) -> dict[str, str]:
    created = utc_now()
    repository_json = json.dumps(repositories, separators=(",", ":"))
    return {
        "spec.md": (
            f"# {title}\n\n**Status:** spec\n**Created:** {created[:10]}\n"
            f"**Ticket:** {ticket}\n\n## Goal\n_To be defined during design._\n\n"
            "## Scope (in / out)\n\n## Success criteria\n\n## Open questions\n"
        ),
        "plan.md": "# plan.md\n\n_To be populated once the spec is clear and approved._\n",
        "notes.md": (
            "---\n"
            f"id: {task_id}\nslug: {slug}\nticket: {ticket}\n"
            f"repositories: {repository_json}\nsize: {size}\nstatus: spec\n"
            f"last-updated: {created}\n---\n\n## Open questions\n\n## Log\n\n"
            f"- {created} - created via agent-memory\n"
        ),
        "review.md": "_Populated by pre-merge. Do not edit by hand._\n",
    }


def create_task(
    root: Path,
    *,
    slug: str,
    title: str,
    ticket: str,
    size: str,
    checkout: Path,
    role: str,
) -> Path:
    if not SLUG_PATTERN.fullmatch(slug):
        raise AgentMemoryError("slug must use YYYY-MM-DD-kebab-case")
    if size not in {"quick", "standard", "big"}:
        raise AgentMemoryError("size must be quick, standard, or big")
    initialize_root(root)
    if any((task_manifest(item) or {}).get("slug") == slug for item in task_directories(root)):
        raise AgentMemoryError(f"task slug already exists: {slug}")
    repo_root = git_root(checkout) or checkout.resolve()
    repo = {"id": repository_id(repo_root), "role": role}
    branch = current_branch(repo_root)
    if branch:
        repo["branch"] = branch
    task_id = f"task_{uuid.uuid4().hex[:20]}"
    task_dir = root / "tasks" / "active" / f"{slug}--{task_id[-8:]}"
    task_dir.mkdir(parents=False, mode=0o700)
    for name, content in task_templates(
        task_id=task_id,
        slug=slug,
        title=title,
        ticket=ticket,
        size=size,
        repositories=[repo],
    ).items():
        (task_dir / name).write_text(content, encoding="utf-8")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "id": task_id,
        "slug": slug,
        "ticket": ticket,
        "status": "active",
        "created_at": utc_now(),
        "repositories": [repo],
    }
    atomic_write_json(task_dir / "task.json", manifest)
    bind_task(root, task_id, repo_root)
    return task_dir


def add_repository(root: Path, reference: str, checkout: Path, role: str) -> Path:
    task_dir = find_task(root, reference, ("active",))
    manifest = task_manifest(task_dir)
    if manifest is None:
        raise AgentMemoryError("task does not have a machine-readable manifest")
    repo_root = git_root(checkout) or checkout.resolve()
    repo_id = repository_id(repo_root)
    repositories = [item for item in manifest.get("repositories", []) if item.get("id") != repo_id]
    repository: dict[str, str] = {"id": repo_id, "role": role}
    branch = current_branch(repo_root)
    if branch:
        repository["branch"] = branch
    repositories.append(repository)
    manifest["repositories"] = repositories
    manifest["updated_at"] = utc_now()
    atomic_write_json(task_dir / "task.json", manifest)
    set_frontmatter(
        task_dir / "notes.md",
        {"repositories": json.dumps(repositories, separators=(",", ":"))},
    )
    bind_task(root, str(manifest["id"]), repo_root)
    return task_dir


def archive_task(root: Path, reference: str) -> Path:
    source = find_task(root, reference, ("active",))
    destination = root / "tasks" / "archive" / source.name
    if destination.exists():
        raise AgentMemoryError(f"archive destination already exists: {destination.name}")
    manifest = task_manifest(source)
    if manifest:
        manifest["status"] = "archived"
        manifest["updated_at"] = utc_now()
        atomic_write_json(source / "task.json", manifest)
    set_frontmatter(
        source / "notes.md",
        {"status": "archived", "last-updated": utc_now()},
    )
    os.replace(source, destination)
    return destination


@dataclasses.dataclass(frozen=True)
class ImportedTask:
    source_store: Path
    source_dir: Path
    repository_id: str
    state: str
    slug: str
    ticket: str
    content_hash: str
    stable_id: str
    missing_files: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class SystemMapFile:
    source_store: Path
    source_file: Path
    repository_id: str
    relative_path: str
    content_hash: str


@dataclasses.dataclass
class MigrationInventory:
    sources: list[Path]
    tasks: list[ImportedTask]
    system_map_files: list[SystemMapFile]
    ignored_entries: list[str]
    exact_groups: list[list[ImportedTask]]
    candidates: list[list[ImportedTask]]
    conflicts: list[list[ImportedTask]]
    system_map_conflicts: list[list[SystemMapFile]]

    @property
    def incomplete(self) -> list[ImportedTask]:
        return [task for task in self.tasks if task.missing_files]

    def summary(self) -> dict[str, int]:
        return {
            "sources": len(self.sources),
            "tasks": len(self.tasks),
            "system_map_files": len(self.system_map_files),
            "ignored_entries": len(self.ignored_entries),
            "exact_duplicate_groups": sum(1 for group in self.exact_groups if len(group) > 1),
            "candidate_groups": len(self.candidates),
            "conflict_groups": len(self.conflicts),
            "system_map_conflicts": len(self.system_map_conflicts),
            "incomplete_tasks": len(self.incomplete),
        }


def source_store(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved.name == ".local" and resolved.is_dir():
        return resolved
    candidate = resolved / ".local"
    if candidate.is_dir():
        return candidate
    raise AgentMemoryError(f"source is not a workflow store or repository: {path}")


def discover_stores(root: Path) -> list[Path]:
    resolved = root.expanduser().resolve()
    if resolved in {Path("/"), Path.home().resolve()}:
        raise AgentMemoryError("discovery root must be narrower than filesystem or home")
    stores: list[Path] = []
    for current, directories, _ in os.walk(resolved, followlinks=False):
        directories[:] = [name for name in directories if name not in SKIP_DISCOVERY_DIRS]
        current_path = Path(current)
        if current_path.name == ".local":
            stores.append(current_path.resolve())
            directories[:] = []
    return stores


def unique_paths(paths: Iterable[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            result.append(resolved)
    return sorted(result)


def inventory(source_paths: Sequence[Path], discovery_roots: Sequence[Path]) -> MigrationInventory:
    sources = [source_store(path) for path in source_paths]
    for root in discovery_roots:
        sources.extend(discover_stores(root))
    sources = unique_paths(sources)
    if not sources:
        raise AgentMemoryError("no workflow stores were found")

    tasks: list[ImportedTask] = []
    system_files: list[SystemMapFile] = []
    ignored: list[str] = []
    for store in sources:
        repo_path = store.parent
        repo_id = repository_id(repo_path)
        for state in ("active", "archive"):
            state_dir = store / state
            if not state_dir.exists():
                continue
            for entry in sorted(state_dir.iterdir()):
                if not entry.is_dir() or not (entry / "notes.md").is_file():
                    ignored.append(f"{store.name}/{state}/{entry.name}")
                    continue
                metadata = parse_frontmatter(entry / "notes.md")
                slug = metadata.get("slug") or entry.name
                ticket = metadata.get("ticket") or metadata.get("linear") or ""
                missing = tuple(name for name in EXPECTED_TASK_FILES if not (entry / name).is_file())
                manifest = task_manifest(entry) or {}
                tasks.append(
                    ImportedTask(
                        source_store=store,
                        source_dir=entry,
                        repository_id=repo_id,
                        state=state,
                        slug=slug,
                        ticket=ticket,
                        content_hash=hash_tree(entry),
                        stable_id=str(manifest.get("id") or metadata.get("id") or ""),
                        missing_files=missing,
                    )
                )
        system_map = store / "system-map"
        if system_map.exists():
            for item in sorted(candidate for candidate in system_map.rglob("*") if candidate.is_file()):
                system_files.append(
                    SystemMapFile(
                        source_store=store,
                        source_file=item,
                        repository_id=repo_id,
                        relative_path=item.relative_to(system_map).as_posix(),
                        content_hash=sha256_bytes(item.read_bytes()),
                    )
                )

    exact_by_key: dict[tuple[str, str], list[ImportedTask]] = {}
    for task in tasks:
        exact_by_key.setdefault((task.slug, task.content_hash), []).append(task)
    exact_groups = list(exact_by_key.values())

    conflict_by_key: dict[tuple[str, str], list[ImportedTask]] = {}
    for task in tasks:
        conflict_by_key.setdefault((task.repository_id, task.slug), []).append(task)
    conflicts = [
        group
        for group in conflict_by_key.values()
        if len({task.content_hash for task in group}) > 1
    ]
    stable_by_id: dict[str, list[ImportedTask]] = {}
    for task in tasks:
        if task.stable_id:
            stable_by_id.setdefault(task.stable_id, []).append(task)
    conflicts.extend(
        group
        for group in stable_by_id.values()
        if len({task.content_hash for task in group}) > 1 and group not in conflicts
    )

    candidate_groups: dict[tuple[str, ...], list[ImportedTask]] = {}
    candidate_by_ticket: dict[str, list[ImportedTask]] = {}
    for task in tasks:
        if task.ticket:
            candidate_by_ticket.setdefault(task.ticket.strip().lower(), []).append(task)
    candidate_by_name: dict[str, list[ImportedTask]] = {}
    for task in tasks:
        name = re.sub(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}-", "", task.slug)
        if name:
            candidate_by_name.setdefault(name, []).append(task)
    for group in [*candidate_by_ticket.values(), *candidate_by_name.values()]:
        if len(group) > 1 and len({task.content_hash for task in group}) > 1:
            key = tuple(sorted(str(task.source_dir) for task in group))
            candidate_groups[key] = group
    candidates = list(candidate_groups.values())

    system_by_destination: dict[tuple[str, str], list[SystemMapFile]] = {}
    for item in system_files:
        system_by_destination.setdefault((item.repository_id, item.relative_path), []).append(item)
    system_conflicts = [
        group
        for group in system_by_destination.values()
        if len({item.content_hash for item in group}) > 1
    ]
    return MigrationInventory(
        sources=sources,
        tasks=tasks,
        system_map_files=system_files,
        ignored_entries=ignored,
        exact_groups=exact_groups,
        candidates=candidates,
        conflicts=conflicts,
        system_map_conflicts=system_conflicts,
    )


def safe_repository_path(root: Path, repo_id: str) -> Path:
    parts = repo_id.split("/")
    if any(not part or part in {".", ".."} for part in parts):
        raise AgentMemoryError("repository identity contains unsafe path components")
    destination = root / "repositories"
    for part in parts:
        destination /= part
    resolved = destination.resolve()
    if not is_relative_to(resolved, (root / "repositories").resolve()):
        raise AgentMemoryError("repository identity escapes the memory root")
    return resolved


def migration_report(inventory_value: MigrationInventory, run_id: str, applied: bool) -> dict[str, Any]:
    def task_value(task: ImportedTask) -> dict[str, Any]:
        return {
            "source_store": str(task.source_store),
            "source_dir": str(task.source_dir),
            "repository_id": task.repository_id,
            "state": task.state,
            "slug": task.slug,
            "ticket": task.ticket,
            "content_hash": task.content_hash,
            "stable_id": task.stable_id,
            "missing_files": list(task.missing_files),
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": utc_now(),
        "applied": applied,
        "summary": inventory_value.summary(),
        "sources": [str(path) for path in inventory_value.sources],
        "tasks": [task_value(task) for task in inventory_value.tasks],
        "ignored_entries": inventory_value.ignored_entries,
        "exact_groups": [[task_value(task) for task in group] for group in inventory_value.exact_groups if len(group) > 1],
        "candidate_groups": [[task_value(task) for task in group] for group in inventory_value.candidates],
        "conflict_groups": [[task_value(task) for task in group] for group in inventory_value.conflicts],
        "system_map_conflicts": [
            [
                {
                    "source_file": str(item.source_file),
                    "repository_id": item.repository_id,
                    "relative_path": item.relative_path,
                    "content_hash": item.content_hash,
                }
                for item in group
            ]
            for group in inventory_value.system_map_conflicts
        ],
    }


def migrated_task_id(group: list[ImportedTask]) -> str:
    stable = {task.stable_id for task in group if task.stable_id}
    if len(stable) == 1:
        return next(iter(stable))
    representative = group[0]
    digest = sha256_bytes(
        f"{representative.slug}\n{representative.content_hash}".encode("utf-8")
    )[:20]
    return f"task_legacy_{digest}"


def apply_migration(
    root: Path,
    inventory_value: MigrationInventory,
    *,
    materialize_missing: bool = False,
) -> dict[str, Any]:
    if inventory_value.conflicts:
        raise AgentMemoryError("migration has divergent task conflicts; inspect the dry-run report")
    if inventory_value.system_map_conflicts:
        raise AgentMemoryError("migration has divergent system-map conflicts; inspect the dry-run report")
    if inventory_value.incomplete and not materialize_missing:
        raise AgentMemoryError("migration has incomplete tasks; inspect the dry-run report")
    for source in inventory_value.sources:
        if root == source or is_relative_to(root, source) or is_relative_to(source, root):
            raise AgentMemoryError("migration destination and source stores must not overlap")

    initialize_root(root)
    lock = root / ".migration.lock"
    try:
        lock.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise AgentMemoryError("another migration appears to be running") from exc

    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-{uuid.uuid4().hex[:8]}"
    staging = root / ".staging" / run_id
    staged_tasks = staging / "tasks"
    staged_system = staging / "repositories"
    source_hashes = {str(task.source_dir): task.content_hash for task in inventory_value.tasks}
    system_source_hashes = {
        str(item.source_file): item.content_hash
        for item in inventory_value.system_map_files
    }
    imported = 0
    skipped = 0
    promotions: list[tuple[Path, Path]] = []
    promoted: list[Path] = []
    try:
        staged_tasks.mkdir(parents=True, mode=0o700)
        staged_system.mkdir(parents=True, mode=0o700)
        existing_tasks = {
            str((task_manifest(path) or {}).get("id")): path
            for path in task_directories(root)
            if task_manifest(path)
        }
        for group in inventory_value.exact_groups:
            task_id = migrated_task_id(group)
            if task_id in existing_tasks:
                existing = task_manifest(existing_tasks[task_id]) or {}
                migrated_hashes = set(
                    existing.get("migration", {}).get("source_hashes", [])
                )
                expected_hashes = {task.content_hash for task in group}
                if not expected_hashes.issubset(migrated_hashes):
                    raise AgentMemoryError(
                        "existing task identity does not match the migration source"
                    )
                skipped += 1
                continue
            representative = group[0]
            state = representative.state
            destination_name = f"{representative.slug}--{task_id[-8:]}"
            staged = staged_tasks / state / destination_name
            staged.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            shutil.copytree(representative.source_dir, staged)
            for missing_file in representative.missing_files:
                (staged / missing_file).write_text(
                    "_Missing from the legacy source; materialized during migration._\n",
                    encoding="utf-8",
                )
            repositories = sorted(
                {task.repository_id for task in group}
            )
            repository_values = [{"id": repo, "role": "imported"} for repo in repositories]
            notes = staged / "notes.md"
            ticket = representative.ticket
            set_frontmatter(
                notes,
                {
                    "id": task_id,
                    "ticket": ticket,
                    "repositories": json.dumps(repository_values, separators=(",", ":")),
                },
                remove={"linear"},
            )
            manifest = {
                "schema_version": SCHEMA_VERSION,
                "id": task_id,
                "slug": representative.slug,
                "ticket": ticket,
                "status": state,
                "created_at": parse_frontmatter(notes).get("last-updated", utc_now()),
                "repositories": repository_values,
                "migration": {
                    "source_hashes": sorted({task.content_hash for task in group}),
                    "source_count": len(group),
                    "materialized_files": list(representative.missing_files),
                },
            }
            atomic_write_json(staged / "task.json", manifest)
            destination = root / "tasks" / state / destination_name
            if destination.exists():
                raise AgentMemoryError(f"migration destination collision: {destination_name}")
            promotions.append((staged, destination))
            existing_tasks[task_id] = staged

        system_destinations: set[tuple[str, str]] = set()
        for item in inventory_value.system_map_files:
            key = (item.repository_id, item.relative_path)
            if key in system_destinations:
                continue
            system_destinations.add(key)
            destination = safe_repository_path(root, item.repository_id) / "system-map" / item.relative_path
            if destination.exists():
                if sha256_bytes(destination.read_bytes()) != item.content_hash:
                    raise AgentMemoryError("system-map destination changed during migration")
                skipped += 1
                continue
            staged = safe_repository_path(staging, item.repository_id) / "system-map" / item.relative_path
            staged.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            shutil.copy2(item.source_file, staged)
            promotions.append((staged, destination))

        for task in inventory_value.tasks:
            if hash_tree(task.source_dir) != source_hashes[str(task.source_dir)]:
                raise AgentMemoryError("a source task changed during migration")
        for item in inventory_value.system_map_files:
            if (
                sha256_bytes(item.source_file.read_bytes())
                != system_source_hashes[str(item.source_file)]
            ):
                raise AgentMemoryError("a source system-map file changed during migration")

        for staged, destination in promotions:
            destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            os.replace(staged, destination)
            promoted.append(destination)
            imported += 1

        report = migration_report(inventory_value, run_id, applied=True)
        report["result"] = {"imported": imported, "skipped": skipped}
        atomic_write_json(root / "migrations" / run_id / "report.json", report)
        return report
    except Exception:
        for destination in reversed(promoted):
            if destination.is_dir():
                shutil.rmtree(destination)
            elif destination.exists():
                destination.unlink()
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)
        try:
            lock.rmdir()
        except OSError:
            pass


def print_value(value: Any, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(value, sort_keys=True))
    else:
        print(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-memory")
    parser.add_argument("--root", type=Path, help="override the resolved memory root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    root_parser = subparsers.add_parser("root", help="print the resolved memory root")
    root_parser.add_argument("--repo", type=Path, default=Path.cwd())
    root_parser.add_argument("--legacy-fallback", action="store_true")

    repo_parser = subparsers.add_parser("repo-id", help="print a canonical repository identity")
    repo_parser.add_argument("path", type=Path, nargs="?", default=Path.cwd())

    system_map_parser = subparsers.add_parser(
        "system-map", help="print the repository-scoped system-map path"
    )
    system_map_parser.add_argument("--repo", type=Path, default=Path.cwd())

    create_parser = subparsers.add_parser("create", help="create a task in central memory")
    create_parser.add_argument("--slug", required=True)
    create_parser.add_argument("--title", required=True)
    create_parser.add_argument("--ticket", default="")
    create_parser.add_argument("--size", choices=("quick", "standard", "big"), default="standard")
    create_parser.add_argument("--repo", type=Path, default=Path.cwd())
    create_parser.add_argument("--role", default="primary")

    add_repo_parser = subparsers.add_parser("add-repo", help="attach a repository to a task")
    add_repo_parser.add_argument("task")
    add_repo_parser.add_argument("--repo", type=Path, required=True)
    add_repo_parser.add_argument("--role", required=True)

    bind_parser = subparsers.add_parser("bind", help="bind a checkout to an active task")
    bind_parser.add_argument("task")
    bind_parser.add_argument("--repo", type=Path, default=Path.cwd())
    bind_parser.add_argument("--branch")

    current_parser = subparsers.add_parser("current", help="resolve the current active task")
    current_parser.add_argument("--repo", type=Path, default=Path.cwd())
    current_parser.add_argument("--task")

    list_parser = subparsers.add_parser("list", help="list task directories")
    list_parser.add_argument("--state", choices=("active", "archive", "all"), default="active")

    archive_parser = subparsers.add_parser("archive", help="move an active task to archive")
    archive_parser.add_argument("task")

    migrate_parser = subparsers.add_parser("migrate", help="inventory or migrate legacy stores")
    migrate_parser.add_argument("--source", type=Path, action="append", default=[])
    migrate_parser.add_argument("--discover-root", type=Path, action="append", default=[])
    migrate_parser.add_argument("--apply", action="store_true")
    migrate_parser.add_argument(
        "--materialize-missing",
        action="store_true",
        help="create explicit placeholders for missing legacy task files",
    )
    migrate_parser.add_argument("--report", type=Path)
    migrate_parser.add_argument("--json", action="store_true")
    return parser


def selected_root(args: argparse.Namespace, repository: Path | None = None) -> Path:
    if args.root:
        return validate_memory_root(args.root, repository=repository)
    return resolve_memory_root(repository=repository)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "root":
            if args.root:
                root = validate_memory_root(args.root, repository=args.repo)
            else:
                root = resolve_memory_root(
                    repository=args.repo, legacy_fallback=args.legacy_fallback
                )
            print(root)
            return 0
        if args.command == "repo-id":
            print(repository_id(args.path))
            return 0

        repository = getattr(args, "repo", Path.cwd())
        root = selected_root(args, repository)
        if args.command == "system-map":
            print(safe_repository_path(root, repository_id(args.repo)) / "system-map")
        elif args.command == "create":
            print(
                create_task(
                    root,
                    slug=args.slug,
                    title=args.title,
                    ticket=args.ticket,
                    size=args.size,
                    checkout=args.repo,
                    role=args.role,
                )
            )
        elif args.command == "add-repo":
            print(add_repository(root, args.task, args.repo, args.role))
        elif args.command == "bind":
            task_dir = find_task(root, args.task, ("active",))
            manifest = task_manifest(task_dir)
            if not manifest:
                raise AgentMemoryError("task does not have a machine-readable manifest")
            bind_task(root, str(manifest["id"]), args.repo, args.branch)
            print(task_dir)
        elif args.command == "current":
            print(resolve_current_task(root, args.repo, args.task))
        elif args.command == "list":
            states = ("active", "archive") if args.state == "all" else (args.state,)
            for task_dir in task_directories(root, states):
                print(task_dir)
        elif args.command == "archive":
            print(archive_task(root, args.task))
        elif args.command == "migrate":
            if args.materialize_missing and not args.apply:
                raise AgentMemoryError("--materialize-missing requires --apply")
            inventory_value = inventory(args.source, args.discover_root)
            run_id = "dry-run"
            if args.apply:
                report = apply_migration(
                    root,
                    inventory_value,
                    materialize_missing=args.materialize_missing,
                )
            else:
                report = migration_report(inventory_value, run_id, applied=False)
            if args.report:
                atomic_write_json(args.report.expanduser().resolve(), report)
            summary = report["summary"]
            if args.apply:
                summary = {**summary, **report.get("result", {})}
            print_value(summary, args.json)
        else:
            parser.error("unknown command")
        return 0
    except AgentMemoryError as exc:
        print(f"agent-memory: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
