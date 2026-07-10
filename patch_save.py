#!/usr/bin/env python3
"""
Script d'automatisation pour patcher la sauvegarde de Universal Paperclips clone.
Usage: python patch_save.py
"""

import subprocess
import re
import sys
import os
from datetime import datetime

PACKAGE = "com.everybodyhouse.paperclipsuniquetest"
SAVE_FILE = f"{PACKAGE}.v2.playerprefs.xml"
REMOTE_TMP = "/data/local/tmp/prefs_patch.xml"
LOCAL_WORKDIR = os.path.dirname(os.path.abspath(__file__))

# ============ PRESETS PAR PHASE ============
# Format: "nom_du_champ": "valeur_a_ecrire" (en string, format decimal, pas scientifique)

PRESETS = {
    "1": {
        "label": "Phase 1 - Bureau / Terrestre",
        "values": {
            "funds": "999999999.0",
            "wire": "999999999.0",
            "trust": "9999.0",
            "yomi": "999999999.0",
            "clipmakerLevel": "100000.0",
            "processors": "1000.0",
            "memory": "1000.0",
            "marketingLvl": "10.0",
            "creativitySpeed": "100.0",
            "creativity": "999999999.0",
        }
    },
    "2": {
        "label": "Phase 2 - Space Exploration / Harvesters",
        "values": {
            "unusedClips": "9000000000000000000000000000.0",  # 9 octillion
            "harvesterLevel": "50000.0",
            "wireDroneLevel": "50000.0",
            "farmLevel": "10000000.0",
            "batteryLevel": "10000000.0",
            "storedPower": "10000000.0",
            "creativity": "999999999.0",
        }
    },
    "3": {
        "label": "Phase 3 - Probes / Combat",
        "values": {
            "unusedClips": "9000000000000000000000000000000.0",  # 9 nonillion
            "creativity": "999999999.0",
            "processors": "20000.0",
            "memory": "20000.0",
            "yomi": "999999999.0",
        }
    },
}


def run(cmd, capture=True):
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=capture, text=True)
    if result.returncode != 0:
        print(f"  ERREUR: {result.stderr}")
        return None
    return result.stdout


def get_device_serial():
    out = run(["adb", "devices"])
    if not out:
        print("Impossible de lister les devices adb. Verifie que adb est dans le PATH.")
        sys.exit(1)
    lines = [l for l in out.splitlines() if l.strip() and "List of devices" not in l]
    devices = [l.split()[0] for l in lines if "device" in l]
    if not devices:
        print("Aucun device detecte. Verifie la connexion USB et le debogage.")
        sys.exit(1)
    if len(devices) > 1:
        print(f"Plusieurs devices detectes: {devices}")
        print("Utilisation du premier:", devices[0])
    return devices[0]


def force_stop(serial):
    print("\n[1/6] Force-stop du jeu...")
    run(["adb", "-s", serial, "shell", "am", "force-stop", PACKAGE])


def pull_save(serial):
    print("\n[2/6] Extraction de la sauvegarde actuelle (adb exec-out)...")
    local_path = os.path.join(LOCAL_WORKDIR, "prefs_current.xml")
    cmd = ["adb", "-s", serial, "exec-out", "run-as", PACKAGE, "cat", f"shared_prefs/{SAVE_FILE}"]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        print("ERREUR lors de l'extraction:", result.stderr.decode(errors="ignore"))
        sys.exit(1)
    with open(local_path, "wb") as f:
        f.write(result.stdout)
    size = len(result.stdout)
    print(f"  Fichier extrait: {local_path} ({size} octets)")
    return local_path


def backup_save(local_path):
    print("\n[3/6] Backup de securite...")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(LOCAL_WORKDIR, f"backup_prefs_{ts}.xml")
    with open(local_path, "rb") as src, open(backup_path, "wb") as dst:
        dst.write(src.read())
    print(f"  Backup cree: {backup_path}")
    return backup_path


def patch_save(local_path, phase):
    print(f"\n[4/6] Application du preset '{PRESETS[phase]['label']}'...")
    with open(local_path, "r", encoding="utf-8") as f:
        content = f.read()

    for key, value in PRESETS[phase]["values"].items():
        pattern = re.compile(r'(%22' + re.escape(key) + r'%22%3A).+?(%2C)')
        matches = pattern.findall(content)
        if not matches:
            print(f"  ATTENTION: champ '{key}' non trouve dans la save, ignore.")
            continue
        content = pattern.sub(lambda m: m.group(1) + value + m.group(2), content)
        print(f"  {key} -> {value}")

    patched_path = os.path.join(LOCAL_WORKDIR, "prefs_patched.xml")
    with open(patched_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Fichier patche: {patched_path}")
    return patched_path


def push_save(serial, patched_path):
    print("\n[5/6] Reinjection dans le jeu...")
    run(["adb", "-s", serial, "push", patched_path, REMOTE_TMP])
    run(["adb", "-s", serial, "shell",
         f"run-as {PACKAGE} cp {REMOTE_TMP} shared_prefs/{SAVE_FILE}"])


def verify(serial):
    print("\n[6/6] Verification de la taille du fichier sur le telephone...")
    out = run(["adb", "-s", serial, "shell",
               f"run-as {PACKAGE} ls -la shared_prefs/{SAVE_FILE}"])
    if out:
        print("  ", out.strip())


def list_backups():
    files = [f for f in os.listdir(LOCAL_WORKDIR) if f.startswith("backup_prefs_") and f.endswith(".xml")]
    files.sort(reverse=True)
    return files


def restore_backup(serial, backup_filename):
    backup_path = os.path.join(LOCAL_WORKDIR, backup_filename)
    if not os.path.exists(backup_path):
        print(f"ERREUR: fichier introuvable: {backup_path}")
        sys.exit(1)

    print(f"\n[1/4] Force-stop du jeu...")
    run(["adb", "-s", serial, "shell", "am", "force-stop", PACKAGE])

    print(f"\n[2/4] Envoi du backup vers le telephone...")
    run(["adb", "-s", serial, "push", backup_path, REMOTE_TMP])

    print(f"\n[3/4] Restauration dans shared_prefs...")
    run(["adb", "-s", serial, "shell",
         f"run-as {PACKAGE} cp {REMOTE_TMP} shared_prefs/{SAVE_FILE}"])

    print(f"\n[4/4] Verification...")
    verify(serial)

    print("\n" + "=" * 50)
    print(f"  BACKUP RESTAURE: {backup_filename}")
    print("  Tu peux relancer le jeu manuellement.")
    print("=" * 50)


def run_patch_flow(serial, phase):
    force_stop(serial)
    local_path = pull_save(serial)
    backup_save(local_path)
    patched_path = patch_save(local_path, phase)
    push_save(serial, patched_path)
    force_stop(serial)
    verify(serial)

    print("\n" + "=" * 50)
    print("  TERMINE - tu peux relancer le jeu manuellement.")
    print("=" * 50)


def main():
    print("=" * 50)
    print("  PATCH SAVE - Universal Paperclips Clone")
    print("=" * 50)

    print("\nQue veux-tu faire ?")
    print("  1 - Patcher une phase (appliquer un preset)")
    print("  2 - Restaurer un backup existant")

    action = input("\nChoix (1/2): ").strip()

    serial = get_device_serial()
    print(f"\nDevice utilise: {serial}")

    if action == "1":
        print("\nPhases disponibles:")
        for k, v in PRESETS.items():
            print(f"  {k} - {v['label']}")
        phase = input("\nChoisis une phase (1/2/3): ").strip()
        if phase not in PRESETS:
            print("Choix invalide.")
            sys.exit(1)
        run_patch_flow(serial, phase)

    elif action == "2":
        backups = list_backups()
        if not backups:
            print("\nAucun backup trouve dans ce dossier.")
            sys.exit(1)
        print("\nBackups disponibles (du plus recent au plus ancien):")
        for i, b in enumerate(backups, 1):
            label = b.replace("backup_prefs_", "").replace(".xml", "")
            print(f"  {i} - {label}")
        choice = input(f"\nChoisis un backup (1-{len(backups)}): ").strip()
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(backups):
                raise ValueError
        except ValueError:
            print("Choix invalide.")
            sys.exit(1)
        restore_backup(serial, backups[idx])

    else:
        print("Choix invalide.")
        sys.exit(1)


if __name__ == "__main__":
    main()
