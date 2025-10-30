# 🏔️ Bike Scenario Planner

A minimalist, dependency-free **Python CLI** to plan and compare custom mountain bike builds.

You can:
- Interactively pick one model per category (fork, wheelset, drivetrain, etc.)
- Instantly see total weight and cost
- Clone or load saved scenarios
- Import from a simple YAML/JSON file
- Append new components to the database with a guided prompt

Everything runs locally, no external packages required.

---

## 🗂️ Folder structure

```
/mnt/data/
├── bike_scenarios.py     # CLI tool (main entry point)
├── parts.csv             # Lightweight "database" of all available parts
├── /scenarios/           # Saved JSON scenarios
└── /reports/             # Exported Markdown & CSV reports (Obsidian-ready)
```

---

## ⚙️ Running the tool

### 1. Interactive mode
```bash
python bike_scenarios.py
```
You’ll be asked to:
- Choose a **scenario name**
- Pick parts per category
- See total weight/cost live
- Save your scenario as JSON, Markdown, and CSV

**Navigation:**
- Enter a number → select a part  
- `s` → search by brand/model text  
- `Enter` → skip / keep previous choice (when cloning)

---

### 2. Clone your previous scenario
Re-use the last saved scenario as a base:
```bash
python bike_scenarios.py --clone-last --name Ultra-Light-v2 --auto-save
```
→ Instantly opens the last setup, lets you tweak only what you change.

---

### 3. Load a scenario from YAML or JSON
You can describe a build declaratively:

`ultra_light.yaml`
```yaml
Fork: Reba RL
Wheelset: XR 1700 SPLINE 29
Drivetrain: SLX M7100 1x12
Brakes: SLX M7100 (pair)
Rotors: RT66 (pair)
BottomBracket: BB-MT800-T47
TyreFront: Barzo
TyreRear: Mezcal
CockpitBar: WCS Flat Trail
CockpitStem: Elite X4
Seatpost: Elite
```

Then run:
```bash
python bike_scenarios.py --scenario ultra_light.yaml --save
```

Outputs:
- `/scenarios/ultra_light.json` → structured data
- `/reports/ultra_light.md` → Markdown summary (Obsidian-ready)
- `/reports/ultra_light.csv` → spreadsheet summary

---

### 4. Add new parts interactively
Append to your local database:
```bash
python bike_scenarios.py --add-part
```
Prompts for category, brand, model, weight, and price.

Your part is added to `parts.csv`, immediately available for future builds.

---

## 🧾 parts.csv format

Comma-separated text file — one line per component.

| category | brand | model | variant | weight_g | price_sgd | notes | source | link |
|-----------|--------|--------|----------|-----------|-----------|--------|--------|------|
| Fork | RockShox | Reba RL | 100-120mm Boost | 1650 | 689 | Light XC fork | Tay Junction | |
| Wheelset | DT Swiss | XR1700 SPLINE 29 | 25mm int | 1672 | 1250 | Alloy, 350 hubs | Local SG | |

Add new categories freely — the tool groups automatically by whatever name you use.

---

## 🧮 Output example (Markdown)

```
# Scenario: Ultra-Light-v2

| Category | Brand | Model | Variant | Weight (g) | Price (SGD) |
|-----------|--------|--------|----------|-----------:|-----------:|
| Fork | RockShox | Reba RL | 100-120mm Boost | 1650 | 689 |
| Wheelset | DT Swiss | XR1700 SPLINE 29 | 25mm int | 1672 | 1250 |
| ... |

**Totals:** 9 240 g,  $3 990 SGD
```

---

## 🧠 Design principles

| Concept | Description |
|----------|--------------|
| **Zero dependencies** | Only built-in Python modules (csv, json, os, glob, etc.) |
| **Composable data** | `parts.csv` is the only “database”; you can edit it manually or script it. |
| **Transparent formats** | Scenarios and reports are simple JSON, CSV, and Markdown. |
| **Extendability** | New commands can be added by inserting CLI flags in `main()` or by subclassing helper functions. |
| **Offline-friendly** | No internet or API calls required. |
| **Obsidian integration** | Markdown reports drop directly into your vault. |

---

## 🔧 Future extension ideas

| Feature | How to integrate |
|----------|------------------|
| **Category filters** | Add flag `--only Fork,Wheelset` to limit interactive selection |
| **Weight/price normalization** | Add average and range calculation functions |
| **Multi-bike comparison** | Add `/reports/comparison.md` showing multiple scenarios side-by-side |
| **Export to Excel** | Use `openpyxl` to generate `.xlsx` reports |
| **GUI/TUI** | Wrap selection loop with `textual` or `curses` |
| **Python API** | Expose `load_parts()`, `save_scenario()`, and `summarize()` as importable functions |

---

## 🧩 Quick reference: CLI flags

| Flag | Purpose |
|------|----------|
| `--clone-last` | Start from most recent scenario |
| `--name=<str>` | Name of the scenario to save |
| `--auto-save` | Skip confirmation prompt |
| `--scenario=<file>` | Load parts from YAML or JSON |
| `--save` | Save reports when loading from file |
| `--add-part` | Add a new part interactively |

---

## 🧭 Example workflow

```bash
# Add your own frame, fork, or component
python bike_scenarios.py --add-part

# Build interactively
python bike_scenarios.py --name Climber-01

# Tweak and save variant
python bike_scenarios.py --clone-last --name Climber-02 --auto-save

# Generate directly from YAML file
python bike_scenarios.py --scenario fast_touring.yaml --save
```

---

## 🧑‍💻 Author Notes

This system is intentionally **minimalist** to stay resilient in remote, offline, or field conditions (like during an ultra-distance expedition prep).  
Every output is text-based and easy to archive, version-control, or drop into Obsidian.
