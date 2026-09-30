"""Local-only CLI with atomic result writes and named errors."""
import argparse
import json
import os
from pathlib import Path
import tempfile
from .core import SchedulerError, schedule, validate
from .fixtures import encode, generate
from .report import render


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SchedulerError(f"ParseError: {path}: line {exc.lineno}: {exc.msg}") from exc
    except (OSError, UnicodeError) as exc:
        raise SchedulerError(f"InputError: {path}: line 1: {exc}; use ks fixtures --out demo") from exc


def load(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise SchedulerError(f"MissingInput: {directory}; use ks fixtures --out demo")
    files = sorted(directory.glob("input.*"))
    if not files:
        if any(directory.iterdir()):
            raise SchedulerError(f"MissingInput: {directory}/input.json; expected input.json")
        return {"synthetic": False, "source": "Empty local directory; no records", "as_of": "1970-01-01", "tasks": [], "agents": [], "tools": []}
    if len(files) != 1 or files[0].name != "input.json":
        raise SchedulerError(f"SchemaError: {directory}: input format: exactly one input.json is supported")
    data = read_json(files[0])
    try:
        return validate(data)
    except SchedulerError as exc:
        raise SchedulerError(f"{exc}; file {files[0]}, line 1 (schema location identified by field)") from exc


def atomic_write(path, content):
    path = Path(path)
    temp = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as stream:
            temp = Path(stream.name)
            stream.write(content)
        os.replace(temp, path)
    except OSError as exc:
        raise SchedulerError(f"WriteError: {path}: {exc}") from exc
    finally:
        if temp is not None and temp.exists():
            temp.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(prog="ks", description="Compute local deterministic agent and tool allocations. No execution or predicted savings.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("fixtures", help="Generate labelled synthetic data", epilog="Example: ks fixtures --out demo")
    p.add_argument("--out", required=True)
    for name, help_text in (("run", "Allocate tasks and save results"), ("validate", "Check task and resource schema"), ("capacity", "Show declared agent and tool capacity")):
        p = sub.add_parser(name, help=help_text, description=help_text, epilog=f"Example: ks {name} --input demo")
        p.add_argument("--input", required=True)
        if name == "run":
            p.add_argument("--results", default=".ks/results.json")
    p = sub.add_parser("report", help="Render saved allocations with provenance", epilog="Example: ks report --format md")
    p.add_argument("--format", choices=("md", "json"), default="md")
    p.add_argument("--results", default=".ks/results.json")
    p.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print("Generated 200 labelled SYNTHETIC tasks; expectations are hand-computed.")
        elif args.command == "report":
            result = read_json(Path(args.results))
            try:
                content = render(result, args.format)
            except (KeyError, TypeError) as exc:
                raise SchedulerError(f"SchemaError: {args.results}: invalid result field {exc}") from exc
            if args.output:
                atomic_write(args.output, content)
            else:
                print(content, end="")
        else:
            data = load(args.input)
            if args.command == "validate":
                print("Schema valid. Provenance: " + ("SYNTHETIC" if data["synthetic"] else "operator-declared real input"))
            elif args.command == "capacity":
                print(encode({"synthetic": data["synthetic"], "source": data["source"], "label": "Declared capacity, not measured runtime", "agents": data["agents"], "tools": data["tools"]}), end="")
            else:
                result = schedule(data)
                atomic_write(args.results, encode(result))
                print(render(result, "json"), end="")
        return 0
    except (SchedulerError, OSError) as exc:
        print(str(exc).replace(chr(0x2014), "-"), file=__import__("sys").stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
