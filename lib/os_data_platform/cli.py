import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from .config.registry import load_config


def cmd_validate(args: argparse.Namespace) -> int:
    paths = _collect_yaml_paths(args.paths)
    if not paths:
        print("No YAML files found.", file=sys.stderr)
        return 1

    failures = 0
    for path in paths:
        try:
            cfg = load_config(path)
            print(f"OK   {path}  (type={cfg.type}, id={cfg.id})")
        except ValidationError as e:
            failures += 1
            print(f"FAIL {path}")
            for err in e.errors():
                loc = ".".join(str(x) for x in err["loc"])
                print(f"       {loc}: {err['msg']}")
        except Exception as e:
            failures += 1
            print(f"FAIL {path}: {type(e).__name__}: {e}")

    total = len(paths)
    if failures:
        print(
            f"\n{failures} of {total} config(s) failed validation.",
            file=sys.stderr,
        )
        return 1
    print(f"\nAll {total} config(s) valid.")
    return 0


def _collect_yaml_paths(inputs: list[str]) -> list[Path]:
    out: list[Path] = []
    for raw in inputs:
        p = Path(raw)
        if p.is_dir():
            out.extend(sorted(p.rglob("*.yaml")))
            out.extend(sorted(p.rglob("*.yml")))
        elif p.is_file():
            out.append(p)
        else:
            print(f"warning: path does not exist: {p}", file=sys.stderr)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="os-data-platform")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="Validate YAML config file(s)")
    p_validate.add_argument(
        "paths", nargs="+", help="Config file(s) or directory of configs"
    )
    p_validate.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
