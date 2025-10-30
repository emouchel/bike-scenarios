#!/usr/bin/env python3
# Bike Scenario Planner — Enhanced CLI
# Features:
# - Interactive selection per category (search, pick, skip)
# - Non-interactive mode: --scenario /path/to/scenario.yaml (or .json)
# - Clone last scenario: --clone-last (preselects from the most recent saved)
# - Add new part helper: --add-part (prompts and appends to parts.csv)
# - Saves JSON + Markdown + CSV reports

import os, sys, csv, json, glob, datetime
from typing import Dict, List

BASE = os.path.dirname(os.path.abspath(__file__))
PARTS_CSV = os.path.join(BASE, "parts.csv")
SCEN_DIR = os.path.join(BASE, "scenarios")
REPORT_DIR = os.path.join(BASE, "reports")
os.makedirs(SCEN_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

ANSI = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "green": "\033[32m",
    "cyan": "\033[36m",
    "yellow": "\033[33m",
    "magenta": "\033[35m",
}

def load_parts(path: str) -> List[dict]:
    parts = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["weight_g"] = float(row.get("weight_g",0) or 0)
            row["price_sgd"] = float(row.get("price_sgd",0) or 0)
            parts.append(row)
    return parts

def group_by_category(parts: List[dict]) -> Dict[str, List[dict]]:
    cats = {}
    for p in parts:
        cats.setdefault(p["category"], []).append(p)
    for k in cats:
        cats[k].sort(key=lambda x: (x["brand"], x["model"]))
    return cats

def print_header():
    print(ANSI["bold"] + "Bike Scenario Planner" + ANSI["reset"])
    print("Database:", PARTS_CSV)
    print()

def list_categories(cats: Dict[str, List[dict]]):
    for i, k in enumerate(sorted(cats.keys()), 1):
        print(f"  {i}. {k} ({len(cats[k])} options)")
    print()

def choose_from_list(options, prompt="Choose # (or 's' to search, Enter to skip): "):
    while True:
        sel = input(prompt).strip()
        if sel == "":
            return None
        if sel.lower() == "s":
            return "SEARCH"
        if sel.isdigit():
            idx = int(sel)
            if 1 <= idx <= len(options):
                return options[idx-1]
        print("Invalid, try again.")

def search_and_choose(options):
    q = input("  Search text (brand/model/variant): ").strip().lower()
    filtered = [o for o in options if q in (o["brand"]+" "+o["model"]+" "+(o.get("variant") or "")).lower()]
    if not filtered:
        print("  No match.")
        return None
    for i, o in enumerate(filtered, 1):
        print(f"    {i}. {o['brand']} {o['model']}  [{o.get('variant','')}]  {o['weight_g']:.0f} g  ${o['price_sgd']:.0f}")
    while True:
        sel = input("  Pick # from results, or Enter to cancel: ").strip()
        if sel == "":
            return None
        if sel.isdigit():
            idx = int(sel)
            if 1 <= idx <= len(filtered):
                return filtered[idx-1]
        print("  Invalid.")

def pick_for_category(cat_name, options, preselect=None):
    print(ANSI["cyan"] + f"\nCategory: {cat_name}" + ANSI["reset"])
    for i, o in enumerate(options, 1):
        print(f"  {i}. {o['brand']} {o['model']}  [{o.get('variant','')}]  {o['weight_g']:.0f} g  ${o['price_sgd']:.0f}")
    if preselect:
        print(f"  (Press Enter to keep current: {preselect['brand']} {preselect['model']})")
    while True:
        choice = choose_from_list(options)
        if choice == "SEARCH":
            choice = search_and_choose(options)
            if choice is None:
                continue
        if choice is None and preselect:
            return preselect
        return choice  # may be None (skip)

def summarize(picks):
    total_w = sum(p["weight_g"] for p in picks.values() if p)
    total_p = sum(p["price_sgd"] for p in picks.values() if p)
    print(ANSI["green"] + f"\nCurrent totals: {total_w:.0f} g,  ${total_p:.0f} SGD" + ANSI["reset"])
    return total_w, total_p

def save_scenario(name, picks, totals):
    data = {
        "name": name,
        "created": datetime.datetime.now().isoformat(timespec="seconds"),
        "picks": {k: v for k, v in picks.items() if v},
        "total_weight_g": totals[0],
        "total_price_sgd": totals[1],
    }
    path = os.path.join(SCEN_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    # Export Markdown
    md = ["# Scenario: " + name, "", "| Category | Brand | Model | Variant | Weight (g) | Price (SGD) |",
          "|---|---|---|---|---:|---:|"]
    for cat, v in data["picks"].items():
        md.append(f"| {cat} | {v['brand']} | {v['model']} | {v.get('variant','')} | {v['weight_g']:.0f} | {v['price_sgd']:.0f} |")
    md.append(f"\n**Totals:** {data['total_weight_g']:.0f} g,  ${data['total_price_sgd']:.0f} SGD\n")
    with open(os.path.join(REPORT_DIR, f"{name}.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    # Export CSV
    csv_path = os.path.join(REPORT_DIR, f"{name}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["category","brand","model","variant","weight_g","price_sgd"])
        for cat, v in data["picks"].items():
            w.writerow([cat, v["brand"], v["model"], v.get("variant",""), int(v["weight_g"]), v["price_sgd"]])
    return path

def load_last_scenario():
    files = sorted(glob.glob(os.path.join(SCEN_DIR, "*.json")), key=os.path.getmtime)
    if not files:
        return None
    with open(files[-1], "r", encoding="utf-8") as f:
        return json.load(f)

def parse_simple_yaml(path):
    # Minimal YAML mapping parser: category: model (one per line)
    # Ignores comments (# ...). Values are a single line string.
    mapping = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): 
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"\'')
                mapping[k] = v
    return mapping

def apply_scenario_mapping(mapping, cats):
    # mapping: {category: model}
    picks = {}
    for cat in sorted(cats.keys()):
        want = mapping.get(cat)
        if not want:
            picks[cat] = None
            continue
        # find by exact model name (brand-agnostic)
        options = cats[cat]
        chosen = None
        for o in options:
            if o["model"].lower() == want.lower() or (o["brand"]+" "+o["model"]).lower() == want.lower():
                chosen = o
                break
        picks[cat] = chosen
    return picks

def add_part_interactive():
    print(ANSI["magenta"] + "\nAdd a new part to parts.csv" + ANSI["reset"])
    fields = [
        ("category", "Category (e.g., Fork, Wheelset, Drivetrain): "),
        ("brand", "Brand: "),
        ("model", "Model: "),
        ("variant", "Variant (e.g., 29x2.35 TLR / 100-120mm Boost): "),
        ("weight_g", "Weight in grams (number): "),
        ("price_sgd", "Price in SGD (number): "),
        ("notes", "Notes (optional): "),
        ("source", "Source/store (optional): "),
        ("link", "Link (optional): ")
    ]
    row = {}
    for key, prompt in fields:
        val = input(prompt).strip()
        if key in ("weight_g", "price_sgd"):
            try:
                val = float(val)
            except:
                val = 0.0
        row[key] = val
    exists = os.path.exists(PARTS_CSV)
    with open(PARTS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["category","brand","model","variant","weight_g","price_sgd","notes","source","link"])
        if not exists:
            w.writeheader()
        w.writerow(row)
    print(ANSI["green"] + "Added to parts.csv" + ANSI["reset"])

def main():
    # Parse very simple CLI flags (no argparse to stay dependency-free)
    args = sys.argv[1:]
    flags = {a for a in args if a.startswith("--")}
    values = {a.split("=",1)[0]: a.split("=",1)[1] for a in args if a.startswith("--") and "=" in a}

    if "--add-part" in flags:
        add_part_interactive()
        return

    parts = load_parts(PARTS_CSV)
    if not parts:
        print("No parts found in parts.csv")
        return
    cats = group_by_category(parts)

    # Non-interactive from scenario file
    scen_file = values.get("--scenario")
    if scen_file:
        mapping = {}
        if scen_file.lower().endswith(".json"):
            with open(scen_file, "r", encoding="utf-8") as f:
                mapping = json.load(f)
        else:
            mapping = parse_simple_yaml(scen_file)
        picks = apply_scenario_mapping(mapping, cats)
        total_w = sum(p["weight_g"] for p in picks.values() if p)
        total_p = sum(p["price_sgd"] for p in picks.values() if p)
        name = os.path.splitext(os.path.basename(scen_file))[0]
        print(f"Scenario from file: {name}")
        for cat, v in picks.items():
            if v:
                print(f"- {cat}: {v['brand']} {v['model']} [{v.get('variant','')}]  {v['weight_g']:.0f} g  ${v['price_sgd']:.0f}")
        print(f"\nTotals: {total_w:.0f} g,  ${total_p:.0f} SGD")
        if "--save" in flags:
            save_scenario(name, picks, (total_w, total_p))
        return

    # Clone last scenario preselects
    preselect = None
    if "--clone-last" in flags:
        last = load_last_scenario()
        if last:
            preselect = last.get("picks", {})

    print_header()
    list_categories(cats)
    scenario_name = values.get("--name") or input("Scenario name (e.g., Ultra-Light-01): ").strip() or "Scenario"

    # Turn preselect dict (if any) into category->part dict
    preselect_objs = {}
    if preselect:
        # map preselected dict (category -> {brand, model, ...}) to actual objects in cats
        for cat, list_opts in cats.items():
            prefer = preselect.get(cat)
            hit = None
            if prefer:
                for o in list_opts:
                    if o["brand"] == prefer.get("brand") and o["model"] == prefer.get("model"):
                        hit = o; break
            preselect_objs[cat] = hit

    picks = {k: None for k in sorted(cats.keys())}
    for cat in sorted(cats.keys()):
        choice = pick_for_category(cat, cats[cat], preselect=preselect_objs.get(cat))
        picks[cat] = choice
        summarize(picks)

    tot = summarize(picks)
    auto_save = ("--auto-save" in flags)
    if auto_save or input("Save scenario? (y/N): ").strip().lower() == 'y':
        path = save_scenario(scenario_name, picks, tot)
        print(ANSI["magenta"] + f"Saved: {path} and reports in {REPORT_DIR}" + ANSI["reset"])

if __name__ == "__main__":
    main()
