#!/usr/bin/env python3
import argparse
import subprocess
import sys
import tempfile
import os
import shutil

parser = argparse.ArgumentParser()
parser.add_argument("--output", required=True)
parser.add_argument("--input", help="Fichier source (bypasse stdin)")
args = parser.parse_args()

mermaid_code = ""

# 1. Lecture directe et stricte en UTF-8
if args.input:
    with open(args.input, "r", encoding="utf-8") as f:
        mermaid_code = f.read()
else:
    raw_bytes = sys.stdin.buffer.read()
    if not raw_bytes.strip():
        sys.exit("ERR: Entrée vide")
    
    for enc in ['utf-8', 'utf-16le', 'cp1252', 'cp850', 'mbcs']:
        try:
            mermaid_code = raw_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue

# Nettoyage des retours à la ligne
mermaid_code = mermaid_code.strip().replace('\r\n', '\n')

# 2. Écriture stricte en UTF-8 pour le binaire Node.js
with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False, encoding="utf-8") as tmp:
    tmp.write(mermaid_code)
    tmp_path = tmp.name

try:
    mmdc_exe = shutil.which("mmdc.cmd" if os.name == "nt" else "mmdc")
    if not mmdc_exe:
        npx_exe = shutil.which("npx.cmd" if os.name == "nt" else "npx")
        if not npx_exe:
            sys.exit("ERR: Node.js (npx) introuvable.")
        cmd = [npx_exe, "-y", "@mermaid-js/mermaid-cli", "-i", tmp_path, "-o", args.output, "-b", "transparent"]
    else:
        cmd = [mmdc_exe, "-i", tmp_path, "-o", args.output, "-b", "transparent"]

    env = os.environ.copy()
    if os.name == "nt":
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if os.path.exists(edge_path):
            env["PUPPETEER_EXECUTABLE_PATH"] = edge_path
        elif os.path.exists(chrome_path):
            env["PUPPETEER_EXECUTABLE_PATH"] = chrome_path

    subprocess.run(cmd, env=env, check=True, capture_output=True)
    print(f"OK: {args.output}")

except subprocess.CalledProcessError as e:
    err_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else "Erreur inconnue"
    print(f"ERR: mmdc crash. {err_msg}")
    sys.exit(1)
finally:
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
    if args.input and os.path.exists(args.input):
        os.remove(args.input)