# 🎵 Duodeca - Official Releases & Binaries

Bienvenue sur le dépôt officiel des releases publiques du projet **Duodeca** (Système Amplificateur / DSP Audio).

Ce dépôt héberge les fichiers compilés prêts à l'emploi (firmwares et application de contrôle).

---

## 📦 Téléchargements (Dernière Version)

👉 Rendez-vous sur la section **[Releases](https://github.com/gotrune/Duodeca-Releases/releases/latest)** pour télécharger les binaires de la dernière version.

### Fichiers disponibles par release :
| Binaire | Cible / Plateforme | Description |
| :--- | :--- | :--- |
| `DuodecaControl-vX.Y.Z-Windows.exe` | Windows 10/11 | Application PC de contrôle (Interface graphique PyQt + Bluetooth SPP) |
| `Firmware-STM32-USB-I2S-vX.Y.Z.bin` | STM32F446 | Firmware USB-to-I2S Audio (format binaire direct) |
| `Firmware-STM32-USB-I2S-vX.Y.Z.hex` | STM32F446 | Firmware USB-to-I2S Audio (format Intel HEX) |
| `Firmware-ESP32-DSP-TFT-vX.Y.Z.bin` | ESP32 | Firmware DSP & Gestion Audio (écran TFT) |
| `checksums.txt` | Tous | Sommes de contrôle SHA-256 pour vérifier l'intégrité des fichiers |

---

## 🚀 Guide d'installation

### 1. Application Windows (`DuodecaControl.exe`)
- Téléchargez `DuodecaControl-vX.Y.Z-Windows.exe`.
- Exécutez le fichier directement (aucun installateur complexe requis).
- Assurez-vous que le Bluetooth de votre PC est activé pour communiquer avec l'amplificateur.

### 2. Firmware STM32F446 (USB to I2S)
Vous pouvez flasher le fichier `.bin` ou `.hex` :
- **Via STM32CubeProgrammer (USB DFU ou ST-Link) :**
  1. Branchez la carte en mode bootloader DFU ou connectez votre ST-Link.
  2. Ouvrez **STM32CubeProgrammer**.
  3. Sélectionnez le fichier `Firmware-STM32-USB-I2S-vX.Y.Z.bin` (adresse de départ : `0x08000000`).
  4. Cliquez sur **Download**.

### 3. Firmware ESP32 (DSP Controller)
- **Via esptool.py :**
  ```bash
  python -m esptool --chip esp32 --baud 921600 write_flash 0x10000 Firmware-ESP32-DSP-TFT-vX.Y.Z.bin
  ```
- **Ou via tout flasher web ESP32 compatible.**

---

## 🔒 Sécurité et Intégrité

Toutes les releases fournissent un fichier `checksums.txt` contenant les empreintes SHA-256 de chaque binaire.  
Pour vérifier un fichier sous Windows PowerShell :
```powershell
Get-FileHash nom_du_fichier -Algorithm SHA256
```
