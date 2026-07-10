# Paperclip Save Editor

Outil d'automatisation pour patcher la sauvegarde locale (PlayerPrefs) d'un clone Unity
de *Universal Paperclips* (`com.everybodyhouse.paperclipsuniquetest`), à des fins de test/debug
sur un projet étudiant.

Le script fait, en une seule commande :
1. Force-stop du jeu
2. Extraction de la sauvegarde actuelle via `adb exec-out` (fiable, pas de troncature)
3. Backup horodaté automatique avant toute modification
4. Application d'un preset de valeurs selon la phase du jeu choisie (1, 2 ou 3)
5. Réinjection dans le dossier `shared_prefs` de l'app via `run-as`
6. Vérification finale (taille du fichier)

## Prérequis

- **Android Debug Bridge (`adb`)** installé et dans le PATH
  (fourni avec [platform-tools](https://developer.android.com/tools/releases/platform-tools))
- **Python 3.8+**
- Sur le téléphone : **débogage USB** activé (Options développeur), app cible **installée en version debuggable**
  (voir section "Pourquoi debuggable ?" plus bas si le patch APK n'a pas déjà été fait)
- Le jeu doit avoir été lancé **au moins une fois** après installation pour que le dossier `shared_prefs` existe

## Utilisation — PC (Windows/Mac/Linux)

```bash
git clone https://github.com/<ton-user>/paperclip-save-editor.git
cd paperclip-save-editor
python patch_save.py
```

Branche ton téléphone en USB, autorise le débogage si demandé, puis suis les instructions à l'écran
(choix de la phase 1/2/3). Le script détecte automatiquement le device connecté.

## Utilisation — Termux (Android) — expérimental

Cette option est **non garantie** : `adb` doit pouvoir "voir" un appareil Android depuis l'extérieur.
Faire tourner `adb` *sur* le téléphone visé, pour se connecter à lui-même, nécessite le
**débogage sans fil** (Android 11+) couplé en localhost, ce qui ne fonctionne pas sur tous les
firmwares (dépend du fabricant).

```bash
pkg update && pkg install android-tools python git -y
git clone https://github.com/<ton-user>/paperclip-save-editor.git
cd paperclip-save-editor

# Activer le débogage sans fil dans Options développeur > Débogage sans fil
# puis coupler avec le code QR ou le code d'appairage affiché
adb pair 127.0.0.1:<port_appairage>
adb connect 127.0.0.1:<port_connexion>
adb devices   # vérifier qu'un device apparaît

python patch_save.py
```

Si `adb devices` n'affiche rien après le couplage, cette méthode ne fonctionnera pas sur ton
téléphone (limitation du firmware) — dans ce cas, repasser par un PC reste la solution fiable.

## Presets disponibles

| Phase | Contenu |
|---|---|
| 1 | Bureau/terrestre : funds, wire, trust, yomi, clipmakerLevel, processors, memory, marketingLvl, creativitySpeed |
| 2 | Space Exploration : unusedClips, harvesterLevel, wireDroneLevel, farmLevel, batteryLevel, storedPower |
| 3 | Probes/Combat : unusedClips, creativity, processors, memory, yomi |

Les valeurs sont éditables directement dans `patch_save.py` (dictionnaire `PRESETS`).

## Fichiers générés (ignorés par git)

- `prefs_current.xml` — dernière extraction brute
- `prefs_patched.xml` — dernière version patchée avant réinjection
- `backup_prefs_*.xml` — backups horodatés à chaque exécution

## Avertissement

Outil destiné à un usage strictement personnel/éducatif sur une sauvegarde locale que tu contrôles.
Ne modifie que le fichier `shared_prefs` de l'app en local ; n'a aucun effet sur un serveur distant
ou d'autres joueurs.
