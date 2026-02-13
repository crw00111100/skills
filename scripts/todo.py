#!/usr/bin/env python3
"""Simple ToDo List manager with JSON storage.

Usage:
    python3 todo.py <command> [options]

Commands:
    add      --title TITLE [--desc DESC] [--subtasks S1 S2 ...] [--deliverable D] [--deadline YYYY-MM-DD] [--status STATUS] [--file FILE]
    list     [--status STATUS] [--file FILE]
    update   --id ID [--title TITLE] [--desc DESC] [--subtasks S1 S2 ...] [--deliverable D] [--deadline YYYY-MM-DD] [--status STATUS] [--file FILE]
    delete   --id ID [--file FILE]

Status values: pending (default), in_progress, done
Default file: ./todos.json
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone


def load(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save(path, todos):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


STATUS_EMOJI = {"pending": "⏳", "in_progress": "🔄", "done": "✅"}


def print_table(todos, action_msg=None):
    if action_msg:
        print(action_msg)
        print()
    if not todos:
        print("（暂无任务）")
        return
    # Column headers
    headers = ["ID", "任务", "子任务", "交付物", "DDL", "状态"]
    # Build rows
    rows = []
    for t in todos:
        subtasks = "、".join(t.get("subtasks", [])) if t.get("subtasks") else "-"
        deliverable = t.get("deliverable", "") or "-"
        deadline = t.get("deadline", "") or "-"
        status = t.get("status", "pending")
        status_display = f"{STATUS_EMOJI.get(status, '')} {status}"
        rows.append([t["id"][:8], t["title"], subtasks, deliverable, deadline, status_display])
    # Calculate column widths (accounting for CJK characters)
    def display_width(s):
        w = 0
        for c in s:
            w += 2 if ord(c) > 127 else 1
        return w

    col_widths = [max(display_width(headers[i]), *(display_width(r[i]) for r in rows)) for i in range(len(headers))]

    def pad(s, width):
        return s + " " * (width - display_width(s))

    sep = "| " + " | ".join("-" * w for w in col_widths) + " |"
    header_line = "| " + " | ".join(pad(h, col_widths[i]) for i, h in enumerate(headers)) + " |"
    print(header_line)
    print(sep)
    for r in rows:
        print("| " + " | ".join(pad(r[i], col_widths[i]) for i in range(len(headers))) + " |")


def cmd_add(args):
    todos = load(args.file)
    task = {
        "id": uuid.uuid4().hex[:8],
        "title": args.title,
        "description": args.desc or "",
        "subtasks": args.subtasks or [],
        "deliverable": args.deliverable or "",
        "deadline": args.deadline or "",
        "status": args.status,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    todos.append(task)
    save(args.file, todos)
    print_table(todos, f"✅ 已添加任务: {task['title']}")


def cmd_list(args):
    todos = load(args.file)
    if args.status:
        todos = [t for t in todos if t["status"] == args.status]
    msg = f"筛选状态: {args.status}" if args.status else None
    print_table(todos, msg)


def cmd_update(args):
    todos = load(args.file)
    for t in todos:
        if t["id"] == args.id:
            if args.title:
                t["title"] = args.title
            if args.desc is not None:
                t["description"] = args.desc
            if args.subtasks is not None:
                t["subtasks"] = args.subtasks
            if args.deliverable is not None:
                t["deliverable"] = args.deliverable
            if args.deadline is not None:
                t["deadline"] = args.deadline
            if args.status:
                t["status"] = args.status
            t["updated_at"] = now_iso()
            save(args.file, todos)
            print_table(todos, f"✅ 已更新任务: {t['title']}")
            return
    print(f"❌ 未找到任务 '{args.id}'", file=sys.stderr)
    sys.exit(1)


def cmd_delete(args):
    todos = load(args.file)
    original_len = len(todos)
    todos = [t for t in todos if t["id"] != args.id]
    if len(todos) == original_len:
        print(f"❌ 未找到任务 '{args.id}'", file=sys.stderr)
        sys.exit(1)
    save(args.file, todos)
    print_table(todos, f"🗑️ 已删除任务: {args.id}")


def main():
    parser = argparse.ArgumentParser(description="ToDo List Manager")
    sub = parser.add_subparsers(dest="command", required=True)

    # add
    p_add = sub.add_parser("add")
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--desc", default="")
    p_add.add_argument("--subtasks", nargs="*", default=[])
    p_add.add_argument("--deliverable", default="")
    p_add.add_argument("--deadline", default="")
    p_add.add_argument("--status", default="pending", choices=["pending", "in_progress", "done"])
    p_add.add_argument("--file", default="./todos.json")

    # list
    p_list = sub.add_parser("list")
    p_list.add_argument("--status", choices=["pending", "in_progress", "done"])
    p_list.add_argument("--file", default="./todos.json")

    # update
    p_upd = sub.add_parser("update")
    p_upd.add_argument("--id", required=True)
    p_upd.add_argument("--title")
    p_upd.add_argument("--desc")
    p_upd.add_argument("--subtasks", nargs="*")
    p_upd.add_argument("--deliverable")
    p_upd.add_argument("--deadline")
    p_upd.add_argument("--status", choices=["pending", "in_progress", "done"])
    p_upd.add_argument("--file", default="./todos.json")

    # delete
    p_del = sub.add_parser("delete")
    p_del.add_argument("--id", required=True)
    p_del.add_argument("--file", default="./todos.json")

    args = parser.parse_args()
    {"add": cmd_add, "list": cmd_list, "update": cmd_update, "delete": cmd_delete}[args.command](args)


if __name__ == "__main__":
    main()
