#!/usr/bin/env python3
"""
Duodeca Automated Release Publisher
Publishes STM32, ESP32 and Windows binaries to the public GitHub Releases repository
without polluting the git repository history.
"""

import os
import sys
import json
import hashlib
import argparse
import mimetypes
import subprocess
from pathlib import Path
from urllib import request, error

# Default GitHub Configuration
GITHUB_OWNER = "gotrune"
GITHUB_REPO = "Duodeca-Releases"

def get_git_credential_token() -> str:
    """Retrieve GitHub token automatically from Git Credential Manager."""
    try:
        proc = subprocess.Popen(
            ["git", "credential", "fill"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        out, _ = proc.communicate(input="protocol=https\nhost=github.com\n", timeout=5)
        for line in out.splitlines():
            if line.startswith("password="):
                return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return ""

def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def github_request(url: str, token: str, method: str = "GET", data: bytes = None, content_type: str = "application/json"):
    req = request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "Duodeca-Release-Publisher")
    if content_type:
        req.add_header("Content-Type", content_type)
    
    try:
        with request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"[ERREUR HTTP {e.code}] {err_msg}", file=sys.stderr)
        raise

def collect_binaries(base_dir: Path, version: str):
    """Locate compiled binaries from project folders."""
    artifacts = {}
    
    # 1. DuodecaControl .exe
    exe_candidates = [
        base_dir / "DuodecaControl" / "pyinstaller" / "dist" / "DuodecaControl.exe",
        base_dir / "DuodecaControl" / "pyinstaller" / "dist" / "Gui_IA_Ampli.exe",
        base_dir / "DuodecaControl" / "dist" / "DuodecaControl.exe",
        base_dir / "DuodecaControl" / "Gui_IA_Ampli.exe",
    ]
    for c in exe_candidates:
        if c.is_file():
            dest_name = f"DuodecaControl-v{version}-Windows.exe"
            artifacts[dest_name] = c
            print(f"[FOUND] PC GUI: {c} -> {dest_name}")
            break
    
    # 2. STM32 Binaries
    stm_bin = base_dir / "USB-to-I2S-Duodeca" / "build" / "USB_TO_I2S.bin"
    stm_hex = base_dir / "USB-to-I2S-Duodeca" / "build" / "USB_TO_I2S.hex"
    if stm_bin.is_file():
        dest = f"Firmware-STM32-USB-I2S-v{version}.bin"
        artifacts[dest] = stm_bin
        print(f"[FOUND] STM32 .bin: {stm_bin} -> {dest}")
    if stm_hex.is_file():
        dest = f"Firmware-STM32-USB-I2S-v{version}.hex"
        artifacts[dest] = stm_hex
        print(f"[FOUND] STM32 .hex: {stm_hex} -> {dest}")
        
    # 3. ESP32 Binaries
    esp_candidates = [
        base_dir / "Dsproamp" / ".pio" / "build" / "esp32dev_tft" / "firmware.bin",
        base_dir / "Dsproamp" / "build" / "firmware.bin",
        base_dir / "Dsproamp" / "firmware_backup.bin",
    ]
    for c in esp_candidates:
        if c.is_file():
            dest = f"Firmware-ESP32-DSP-TFT-v{version}.bin"
            artifacts[dest] = c
            print(f"[FOUND] ESP32 firmware: {c} -> {dest}")
            break
            
    return artifacts

def upload_release_asset(upload_url_template: str, token: str, file_path: Path, asset_name: str):
    # Template looks like: https://uploads.github.com/repos/owner/repo/releases/123/assets{?name,label}
    upload_url = upload_url_template.split("{")[0] + f"?name={asset_name}"
    
    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = "application/octet-stream"
        
    with open(file_path, "rb") as f:
        file_bytes = f.read()
        
    print(f" -> Envoi de {asset_name} ({len(file_bytes) / 1024 / 1024:.2f} Mo)...")
    req = request.Request(upload_url, data=file_bytes, method="POST")
    req.add_header("Authorization", f"token {token}")
    req.add_header("Content-Type", content_type)
    req.add_header("User-Agent", "Duodeca-Release-Publisher")
    
    try:
        with request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"[ERREUR UPLOAD {e.code}] {err_msg}", file=sys.stderr)
        raise

def main():
    parser = argparse.ArgumentParser(description="Publier une release Duodeca sur GitHub")
    parser.add_argument("version", help="Numéro de version (ex: 1.0.0)")
    parser.add_argument("--notes", default="", help="Notes de mise à jour (Markdown)")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""), help="GitHub Personal Access Token")
    parser.add_argument("--owner", default=GITHUB_OWNER, help="Propriétaire du repo GitHub")
    parser.add_argument("--repo", default=GITHUB_REPO, help="Nom du repo GitHub de releases")
    parser.add_argument("--draft", action="store_true", help="Créer la release en mode brouillon")
    parser.add_argument("--prerelease", action="store_true", help="Marquer comme pré-version")
    parser.add_argument("--dry-run", action="store_true", help="Tester la détection des binaires et les checksums sans envoyer à GitHub")
    
    args = parser.parse_args()
    version = args.version.lstrip("v")
    tag_name = f"v{version}"
    
    token = args.token
    if not token:
        token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        token = get_git_credential_token()
        if token:
            print("[AUTH] Jeton GitHub récupéré automatiquement via Git Credential Manager.")
    if not args.dry_run and not token:
        token = input("Entrez votre GitHub Personal Access Token (PAT) : ").strip()
        if not token:
            print("[ERREUR] Un token GitHub est obligatoire pour publier la release.", file=sys.stderr)
            sys.exit(1)
            
    base_dir = Path(__file__).resolve().parent.parent
    staging_dir = Path(__file__).resolve().parent / "staging"
    staging_dir.mkdir(exist_ok=True)
    
    print(f"\n==========================================")
    print(f" DUODECA RELEASE AUTO-PUBLISHER {tag_name}")
    print(f" Cible: {args.owner}/{args.repo}")
    print(f"==========================================\n")
    
    print("[1/4] Recherche des binaires compilés...")
    artifacts = collect_binaries(base_dir, version)
    if not artifacts:
        print("[ERREUR] Aucun binaire trouvé ! Assurez-vous d'avoir compilé au moins un sous-projet.")
        sys.exit(1)
        
    print(f"\n[2/4] Préparation des fichiers et calcul des SHA-256...")
    checksums = []
    ready_files = {}
    
    for final_name, src_path in artifacts.items():
        staged_file = staging_dir / final_name
        # Copie vers staging
        with open(src_path, "rb") as sf, open(staged_file, "wb") as df:
            df.write(sf.read())
            
        sha = compute_sha256(staged_file)
        checksums.append(f"{sha}  {final_name}")
        ready_files[final_name] = staged_file
        print(f" - {final_name} [SHA-256: {sha[:12]}...]")
        
    # Ecriture de checksums.txt
    checksum_file = staging_dir / "checksums.txt"
    checksum_file.write_text("\n".join(checksums) + "\n", encoding="utf-8")
    ready_files["checksums.txt"] = checksum_file
    print(" - checksums.txt généré avec succès.")
    
    if args.dry_run:
        print("\n[DRY RUN] Mode simulation actif : aucun appel réseau effectué.")
        print(f"Fichiers prêts dans {staging_dir} :")
        for f in ready_files:
            print(f" - {f}")
        print("\nTest réussi !")
        return
    
    print(f"\n[3/4] Création de la release sur GitHub ({tag_name})...")
    create_release_url = f"https://api.github.com/repos/{args.owner}/{args.repo}/releases"
    
    body = args.notes if args.notes else (
        f"## 🎵 Duodeca Release {tag_name}\n\n"
        f"### Binaires inclus :\n" +
        "\n".join([f"- `{name}`" for name in ready_files.keys() if name != "checksums.txt"]) +
        "\n\n### Intégrité des fichiers (SHA-256) :\n```text\n" +
        "\n".join(checksums) +
        "\n```\n"
    )
    
    payload = json.dumps({
        "tag_name": tag_name,
        "name": f"Release {tag_name}",
        "body": body,
        "draft": args.draft,
        "prerelease": args.prerelease
    }).encode("utf-8")
    
    release_info = github_request(create_release_url, token, method="POST", data=payload)
    upload_url_template = release_info["upload_url"]
    html_url = release_info["html_url"]
    print(f"[OK] Release créée : {html_url}")
    
    print(f"\n[4/4] Upload des {len(ready_files)} assets vers GitHub Releases...")
    for asset_name, path in ready_files.items():
        upload_release_asset(upload_url_template, token, path, asset_name)
        print(f" [OK] {asset_name} envoyé.")
        
    print(f"\n==========================================")
    print(f" SUCCÈS : Release {tag_name} publiée avec succès !")
    print(f" Lien public : {html_url}")
    print(f"==========================================\n")

if __name__ == "__main__":
    main()
