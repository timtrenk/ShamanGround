#!/usr/bin/env python3
# server/scaffold_builder.py — build Thoth OM v1 scaffold from scaffold_spec.yaml
# Requirements: Python 3.8+ and PyYAML (pip install pyyaml)

import os, sys, yaml, textwrap, pathlib

SPEC_FILE = "scaffold_spec.yaml"

TEMPLATES = {
  "tweet_thread.yaml": 'id: tweet_thread.v1\ndescription: "3-post launch teaser thread"\nschema: { posts: list[string] }\nconstraints: { max_chars_per_post: 280, required: [concrete_next_action_in_post3], mirrors_target: 0.08 }\nstyle: { tone: "confident, grounded, no hype", banlist: ["revolutionary","game-changing","magical"] }\n',
  "product_overview.yaml": 'id: product_overview.v1\ndescription: "1-page product overview"\nschema: { title: string, summary: string, who_it_is_for: list[string], outcomes: list[string], how_it_works: list[string], differentiators: list[string], cta: string }\nconstraints: { length: "400-600 words", mirrors_target: 0.08 }\nstyle: { tone: "clear, engineering-first" }\n',
  "10_step_plan.yaml": 'id: plan10.v1\ndescription: "Deterministic 10-step task plan"\nschema: { steps: list[object], step_fields: ["number","action","owner","duration","dependencies"] }\nconstraints: { require_owner: true, require_next_action: true, mirrors_target: 0.06 }\nstyle: { tone: "directive, no fluff" }\n',
  "faq.yaml": 'id: faq.v1\ndescription: "5 Q/A customer FAQ bound to overview"\nschema: { items: list[object], item_fields: ["q","a"] }\nconstraints: { non_contradiction_with: product_overview.v1, mirrors_target: 0.08 }\nstyle: { tone: "helpful, precise" }\n',
  "readme.yaml": 'id: readme.v1\ndescription: "README for Thoth OM v1"\nschema: { name: string, purpose: string, quickstart: list[string], files: list[string], run_cards: list[string] }\nconstraints: { include_sections: ["Purpose","Files","Quickstart","Run Cards"], mirrors_target: 0.08 }\nstyle: { tone: "grounded, minimal" }\n'
}

def write(p: pathlib.Path, s: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")
    print(f"[write] {p} ({len(s)} bytes)")

def main():
    spec_path = pathlib.Path(SPEC_FILE)
    if not spec_path.exists():
        print(f"ERROR: {SPEC_FILE} not found. Edit it and run again.")
        sys.exit(1)
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))

    # runtime.yaml
    runtime_yaml = f"""version: {spec['engine']['version']}
env: {spec['engine']['env']}
receipts: true
paths:
  outputs_dir: {spec['paths']['outputs_dir']}
  receipts_dir: {spec['paths']['receipts_dir']}
  logs_dir: {spec['paths']['logs_dir']}
defaults:
  sc_k: {spec['defaults']['sc_k']}
  residual_target:
    copy: {spec['defaults']['residual_target']['copy']}
    plan: {spec['defaults']['residual_target']['plan']}
    spec: {spec['defaults']['residual_target']['spec']}
  crown_verify: {str(spec['defaults']['crown_verify']).lower()}
  template_required: {str(spec['defaults']['template_required']).lower()}
policies:
  on_fail: [regenerate_once]
  tie_break: [constraints_score, mirror_residual, logic_score]
"""
    write(pathlib.Path("runtime.yaml"), runtime_yaml)

    # memory pins
    write(pathlib.Path("memory/brand_voice.md"), spec["memory_pins"]["brand_voice"])
    write(pathlib.Path("memory/glossary.md"), spec["memory_pins"]["glossary"])
    write(pathlib.Path("memory/constraints.md"), spec["memory_pins"]["constraints"])

    # templates (optional)
    inc = (spec.get("templates") or {}).get("include") or {}
    if inc:
        tdir = pathlib.Path("templates")
        for name, content in TEMPLATES.items():
            key = name.split(".")[0]  # tweet_thread, product_overview, 10_step_plan, faq, readme
            key = key.replace("10_step_plan", "plan10")
            if inc.get(key, False):
                write(tdir/name, content)
    print("\nDone. Scaffold created.")

if __name__ == "__main__":
    try:
        import yaml  # type: ignore
    except ImportError:
        print("PyYAML is required. Install with: pip install pyyaml")
        sys.exit(1)
    main()
