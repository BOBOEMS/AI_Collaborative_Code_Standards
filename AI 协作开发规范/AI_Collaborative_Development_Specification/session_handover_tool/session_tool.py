#!/usr/bin/env python3
"""Standalone CLI. UTF-8 JSON in/out; prompts are data, never shell code."""
import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from session_handover_tool import SessionClient, ToolError
    from session_handover_tool.adapters import capabilities
    from session_handover_tool.config import absolute, identifier
    from session_handover_tool.sessions import save
else:
    from . import SessionClient, ToolError
    from .adapters import capabilities
    from .config import absolute, identifier
    from .sessions import save


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", help="Absolute path of the unique project session config")
    p.add_argument("--actor", help="Caller identity, checked against the project's operator list")
    commands = p.add_subparsers(dest="command", required=True)
    commands.add_parser("capabilities")
    commands.add_parser("validate")
    q = commands.add_parser("probe"); q.add_argument("--profile", required=True)
    init = commands.add_parser("init", help="Create a readonly project config; never overwrite")
    init.add_argument("--project-id", required=True)
    init.add_argument("--project-root", required=True)
    init.add_argument("--runtime-dir", required=True)
    def select(q):
        q.add_argument("--milestone")
        q.add_argument("--role", choices=list("ABCDE"))
        q.add_argument("--session", help="Exact registered adapter:native_id")
    for name in ("create", "bind", "switch"):
        q = commands.add_parser(name)
        q.add_argument("--profile", required=name == "switch")
        q.add_argument("--milestone", required=name == "switch")
        q.add_argument("--role", choices=list("ABCDE"), required=name == "switch")
        q.add_argument("--request-id")
        if name != "bind":
            q.add_argument("--title", default="")
            q.add_argument("--message-file", help="CLI creation only: initial native inference turn")
        if name != "create":q.add_argument("--native-id", required=name == "bind")
        if name == "bind":q.add_argument("--recover-request")
        if name == "switch":q.add_argument("--confirmed-stopped", action="store_true")
    select(commands.add_parser("inspect"))
    q = commands.add_parser("read"); select(q)
    q.add_argument("--limit", type=int, default=200)
    q.add_argument("--events", action="store_true", help="Include native work events, excluding request headers/system messages")
    q = commands.add_parser("wait"); select(q)
    q.add_argument("--request-id", help="Accepted dispatch to wait for; omit only to observe idle state")
    q.add_argument("--timeout", type=float, default=30, help="Bounded wait seconds, 0..45; timeout does not resend")
    q = commands.add_parser("send")
    select(q)
    q.add_argument("--task-id", required=True)
    q.add_argument("--message-file", required=True)
    q.add_argument("--report-to", action="append", default=[])
    q.add_argument("--record")
    q.add_argument("--request-id")
    q.add_argument("--confirmed-stopped", action="store_true")
    q = commands.add_parser("report")
    for key in ("milestone", "task-id", "sender", "summary-file"):
        q.add_argument("--" + key, required=True)
    q.add_argument("--status", default="delivery", choices=("delivery", "needs_review", "failed", "needs_input"))
    for key in ("record", "commit", "delivery-id"):q.add_argument("--" + key)
    q = commands.add_parser("receipt"); q.add_argument("request_id")
    q = commands.add_parser("sync"); q.add_argument("--output", required=True)
    return p


def message(path):
    try:return absolute(path).read_text(encoding="utf-8-sig") if path else ""
    except OSError as exc:raise ToolError("invalid_request", "Cannot read UTF-8 message file") from exc


def run(args):
    if args.command == "capabilities":return capabilities()
    if not args.config:raise ToolError("invalid_config", "--config is required")
    path = absolute(args.config)
    if args.command == "init":
        if path.exists():raise ToolError("already_exists", "Config already exists; it was not overwritten")
        root = absolute(args.project_root)
        runtime = absolute(args.runtime_dir)
        data = {"schema_version": 1, "project_id": identifier(args.project_id), "project_root": str(root),
            "runtime_dir": str(runtime), "documents_root": str(root),
            "profiles": {"codex-default": {"adapter": "codex_cli", "cwd": ".", "native": {"inherit_model": True}, "connection": {}}},
            "roles": {}, "milestones": {}, "sessions": {}, "authorization": {"reference": "", "allow": []}}
        from session_handover_tool.config import validate
        validate(data)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive open keeps two concurrent init callers from overwriting one another.
        try:
            with path.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(data, stream, ensure_ascii=False, indent=2); stream.write("\n")
        except FileExistsError:raise ToolError("already_exists", "Config already exists") from None
        return {"status": "initialized_readonly", "config": str(path)}
    client = SessionClient(path, actor=args.actor)
    if args.command == "validate":return client.validate()
    if args.command == "probe":return client.probe(args.profile)
    if args.command == "read":return client.read(session=args.session, milestone=args.milestone, role=args.role,
                                                limit=args.limit, include_events=args.events)
    if args.command == "wait":return client.wait(session=args.session, milestone=args.milestone, role=args.role,
                                                request_id=args.request_id, timeout_seconds=args.timeout)
    if args.command == "receipt":return client.receipt(args.request_id)
    if args.command == "sync":return client.sync(args.output)
    if args.command == "inspect":return client.inspect(session=args.session, milestone=args.milestone, role=args.role)
    if args.command in ("create", "bind", "switch"):
        kwargs = {"profile": args.profile, "milestone": args.milestone, "role": args.role, "request_id": args.request_id}
        if args.command == "bind":return client.bind(args.native_id, **kwargs, recover_request=args.recover_request)
        kwargs.update(title=args.title, message=message(args.message_file))
        if args.command == "switch":return client.switch(**kwargs, native_id=args.native_id, confirmed_stopped=args.confirmed_stopped)
        return client.create(**kwargs)
    if args.command == "send":
        return client.send(message(args.message_file), task_id=args.task_id, session=args.session,
            milestone=args.milestone, role=args.role, report_to=args.report_to, request_id=args.request_id,
            confirmed_stopped=args.confirmed_stopped, record=args.record)
    if args.command == "report":
        return client.report(milestone=args.milestone, task_id=args.task_id, sender=args.sender,
            summary=message(args.summary_file), status=args.status, record=args.record, commit=args.commit, delivery_id=args.delivery_id)
    raise ToolError("unsupported", "Unknown command")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):sys.stdout.reconfigure(encoding="utf-8")
    try:
        result = run(parser().parse_args(argv))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 3 if result.get("status") == "partial" else 0
    except ToolError as exc:
        print(json.dumps(exc.as_dict(), ensure_ascii=False, indent=2))
        return 4 if exc.uncertain else 2
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "code": "local_error", "message": type(exc).__name__, "uncertain": False}))
        return 2


if __name__ == "__main__":raise SystemExit(main())
