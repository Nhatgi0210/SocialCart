"""Validate local API schemas/examples, Markdown targets and requirement traceability.

Install scripts/requirements-docs.txt, then run from any directory.
This is static documentation validation, not an application or provider test.
"""
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
import warnings

try:
    import yaml
    from openapi_spec_validator import validate
    from openapi_schema_validator import OAS30Validator
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from jsonschema import RefResolver
except ImportError:
    raise SystemExit("Install documentation tools: python -m pip install -r scripts/requirements-docs.txt")

ROOT = Path(__file__).resolve().parents[1]
spec = yaml.safe_load((ROOT / "docs/api/openapi.yaml").read_text(encoding="utf-8"))
errors = []
validate(spec)
example_count = 0
reference_count = 0
operation_count = 0

def reject_remote(uri):
    raise ValueError(f"Remote schema reference is not allowed: {uri}")

resolver = RefResolver.from_schema(spec, handlers={"http": reject_remote, "https": reject_remote})

def check_example(schema, value, location):
    global example_count
    try:
        OAS30Validator(schema, resolver=resolver, format_checker=OAS30Validator.FORMAT_CHECKER).validate(value)
        example_count += 1
    except Exception as exc:
        errors.append(f"Invalid example {location}: {exc}")

def walk(node, location="root"):
    global reference_count
    if isinstance(node, dict):
        if "$ref" in node:
            pointer = node["$ref"]
            if not pointer.startswith("#/"):
                errors.append(f"Non-local reference at {location}: {pointer}")
            else:
                try:
                    target = spec
                    for part in pointer[2:].split("/"):
                        target = target[part.replace("~1", "/").replace("~0", "~")]
                    reference_count += 1
                except (KeyError, TypeError):
                    errors.append(f"Unresolved reference {pointer}")
        if isinstance(node.get("schema"), dict):
            if "example" in node:
                check_example(node["schema"], node["example"], location)
            for name, example in node.get("examples", {}).items():
                if "value" in example:
                    check_example(node["schema"], example["value"], location + "/" + name)
        if "type" in node and "example" in node:
            check_example(node, node["example"], location)
        for key, value in node.items():
            walk(value, location + "/" + key)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            walk(value, location + f"/{i}")

walk(spec)
markdown_files = [*ROOT.glob("*.md"), *ROOT.joinpath("docs").rglob("*.md"), *ROOT.joinpath(".agents/skills").rglob("SKILL.md")]
link_count = 0
for path in markdown_files:
    for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8-sig")):
        target = target.strip("<>")
        if urlsplit(target).scheme or target.startswith("#"):
            continue
        relative = unquote(target.split("#")[0])
        if not relative:
            continue
        link_count += 1
        if not (path.parent / relative).exists():
            errors.append(f"Missing Markdown target {path.relative_to(ROOT)} -> {target}")

prd = (ROOT / "docs/product-requirements.md").read_text(encoding="utf-8")
acs = set(re.findall(r"\*\*(AC-\d+[a-z]?)\b", prd))
test_plan = (ROOT / "docs/test-plan.md").read_text(encoding="utf-8")
covered = set(re.findall(r"\bAC-\d+[a-z]?\b", test_plan))
for ac in sorted(acs - covered):
    errors.append(f"AC missing from test plan: {ac}")
for ac in sorted(covered - acs):
    errors.append(f"Unknown AC in test plan: {ac}")
plan = (ROOT / "docs/implementation-plan.md").read_text(encoding="utf-8")
tasks = set(re.findall(r"^\| ([A-Z]+-\d+) \|", plan, re.M))
for path, methods in spec["paths"].items():
    for method, operation in methods.items():
        if method not in {"get", "post", "put", "patch", "delete", "head", "options", "trace"}:
            continue
        operation_count += 1
        if operation.get("x-task") not in tasks:
            errors.append(f"Unknown task for {method} {path}")
        for ac in operation.get("x-requirements", []):
            if ac not in acs:
                errors.append(f"Unknown AC for {method} {path}: {ac}")

if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)
print(f"PASS: OpenAPI 3.0.3, {operation_count} operations, {len(spec['components']['schemas'])} schemas")
print(f"PASS: {example_count} schema-valid examples, {reference_count} local references")
print(f"PASS: {link_count} Markdown file targets across {len(markdown_files)} files (anchors/external URLs not checked)")
print(f"PASS: all {len(acs)} PRD ACs traced in test plan; operation task/AC references valid")
print("Static evidence only; application, browser audit and live integrations NOT RUN.")
