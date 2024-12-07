#!/usr/bin/env python3

import argparse
import os
import json
import sys
from flask import Flask, render_template, request
import urwid
from tqdm import tqdm
import yaml
import subprocess

# Flask web application
app = Flask(__name__)

# Tool categories
CATEGORIES = [
    "information-gathering",
    "vulnerability-analysis",
    "web-applications",
    "exploitation-frameworks",
    "password-attacks",
    "wireless-analysis",
    "reverse-engineering",
    "digital-forensics"
]

# Paths
CONFIG_PATH = "/etc/blackarch-toolkit/config.yaml"
LOG_DIR = "/var/log/blackarch-toolkit"
INVENTORY_FILE = "/var/lib/blackarch_installer/tool_inventory.json"

# Ensure required directories exist
os.makedirs(LOG_DIR, exist_ok=True)

def load_config():
    """Load configuration from YAML file."""
    if not os.path.exists(CONFIG_PATH):
        print(f"Config file not found: {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def log_action(action):
    """Log an action to the installation log."""
    log_file = os.path.join(LOG_DIR, "blackarch_installer_full.log")
    with open(log_file, "a") as f:
        f.write(f"{action}\n")

def install_tool(tool):
    """Simulate tool installation."""
    print(f"Installing {tool}...")
    log_action(f"Installed: {tool}")
    # Example installation logic
    subprocess.run(["sudo", "pacman", "-S", tool], check=False)

def install_category(category):
    """Install tools in a specified category."""
    if category not in CATEGORIES:
        print(f"Invalid category: {category}")
        print(f"Available categories: {', '.join(CATEGORIES)}")
        sys.exit(1)
    print(f"Installing tools in category: {category}")
    for tool in tqdm([f"{category}-tool-{i}" for i in range(1, 6)], desc=f"Installing {category} tools"):
        install_tool(tool)
    print(f"Installation complete for category: {category}")

def start_dashboard():
    """Start the web dashboard."""
    print("Starting web dashboard...")
    app.run(debug=True, host="0.0.0.0", port=5000)

@app.route("/")
def dashboard():
    """Render the main dashboard page."""
    return render_template("index.html", categories=CATEGORIES)

@app.route("/install", methods=["POST"])
def dashboard_install():
    """Install a category from the dashboard."""
    category = request.form.get("category")
    if category:
        install_category(category)
        return f"Installation of {category} tools started.", 200
    return "Category not provided.", 400

def start_tui():
    """Start the text-based user interface."""
    def menu(title, choices):
        body = [urwid.Text(title), urwid.Divider()]
        body.extend(urwid.AttrMap(urwid.Button(c, on_press=menu_item_selected), None, focus_map='reversed') for c in choices)
        return urwid.ListBox(urwid.SimpleFocusListWalker(body))

    def menu_item_selected(button):
        response = urwid.Text([f"You selected: {button.label}\n"])
        main.original_widget = urwid.Pile([menu("Main Menu", CATEGORIES), response])
        install_category(button.label)

    main = urwid.Padding(menu("Main Menu", CATEGORIES), left=2, right=2)
    top = urwid.Overlay(main, urwid.SolidFill(u'\N{MEDIUM SHADE}'),
                        align='center', width=('relative', 60),
                        valign='middle', height=('relative', 60),
                        min_width=20, min_height=9)
    urwid.MainLoop(top).run()

def main():
    """Main function to parse arguments and execute commands."""
    parser = argparse.ArgumentParser(description="BlackArch Toolkit")
    parser.add_argument("-c", "--category", help="Specify tool category")
    parser.add_argument("-r", "--resume", action="store_true", help="Resume previous installation")
    parser.add_argument("--dashboard", action="store_true", help="Launch web management interface")
    parser.add_argument("--tui", action="store_true", help="Start text-based user interface")
    parser.add_argument("--config", help="Use custom configuration file")
    args = parser.parse_args()

    if args.config:
        global CONFIG_PATH
        CONFIG_PATH = args.config

    if args.category:
        install_category(args.category)
    elif args.resume:
        print("Resuming previous installation...")
    elif args.dashboard:
        start_dashboard()
    elif args.tui:
        start_tui()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
