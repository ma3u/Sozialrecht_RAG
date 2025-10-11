# Content Download-Anleitung

**Dieses Repository enthält NUR die Funktionalität (Code), NICHT die PDF-Inhalte.**

**PDFs sind zu groß für Git** (~30 MB, 50 Dateien) und müssen separat heruntergeladen werden.

---

## 🚀 Quick Start: Content herunterladen

### Automatisiert (Empfohlen):

```bash
# TODO: Download-Script erstellen
python scripts/download_all_content.py

# Lädt herunter:
# - 13 SGB-Gesetze von gesetze-im-internet.de
# - 34 Fachliche Weisungen von BA + Harald Thomé
# - 1 BMAS Rundschreiben von Tacheles
```

### Manuell:

Siehe detaillierte Anweisungen in der ursprünglichen Anfrage oder:
- `Metadaten/Quellenverzeichnis.txt` - Alle URLs
- Original README hatte Download-Links

---

## 📁 Erwartete Content-Struktur

Nach dem Download sollten Sie haben:

```
Sozialrecht_RAG/
├── Gesetze/                        # 13 PDFs (9.5 MB)
│   ├── SGB_01_Allgemeiner_Teil.pdf
│   ├── SGB_02_Buergergeld.pdf
│   └── ... (SGB 03-14)
│
├── Fachliche_Weisungen/            # 34 PDFs (~20 MB)
│   ├── SGB_I/                      # 5 PDFs
│   ├── SGB_II/                     # 13 PDFs (inkl. Thomé Folien)
│   ├── SGB_III/                    # 7 PDFs
│   └── ... (SGB IV-X)
│
└── Rundschreiben_BMAS/
    └── SGB_XII_Grundsicherung/     # 1 PDF
```

---

## ✅ Validierung

Nach dem Download prüfen:

```bash
# Anzahl PDFs prüfen
find . -name "*.pdf" | wc -l
# Sollte sein: 50

# Gesamtgröße prüfen
du -sh Gesetze/ Fachliche_Weisungen/ Rundschreiben_BMAS/
# Sollte sein: ~30 MB gesamt

# Integritäts-Check
python scripts/validate_content.py
```

---

## 📋 Quellen

Alle PDFs stammen von offiziellen Quellen:
- **Gesetze**: gesetze-im-internet.de (BMJ) - 100% Vertrauenswürdigkeit
- **BA-Weisungen**: arbeitsagentur.de - 95% Vertrauenswürdigkeit
- **Harald Thomé**: harald-thome.de - 85% Vertrauenswürdigkeit
- **BMAS**: tacheles-sozialhilfe.de (Proxy) - 85% Vertrauenswürdigkeit

Details siehe: `Metadaten/QUELLEN_BEWERTUNG_UND_AKTUALITAET.md`

---

## ⚠️ Warum keine PDFs im Git?

**Gründe für Content-Separation**:
1. **Größe**: 30 MB überschreitet Git Best Practices
2. **Updates**: PDFs ändern sich (Gesetzesänderungen)
3. **Lizenz**: Unterschiedliche Lizenzen (Gesetze gemeinfrei, Weisungen nicht-kommerziell)
4. **Bandbreite**: Nicht jeder braucht alle PDFs

**Lösung**: Git LFS oder separater Content-Server (geplant)

---

## 🔄 Alternativen

### Option 1: Git LFS (Large File Storage)
```bash
git lfs install
git lfs track "*.pdf"
# Dann PDFs hochladen
```

### Option 2: Separates Content-Repository
```bash
# Erstelle: Sozialrecht_RAG_Content (privates Repo)
# Nur für PDFs, keine Funktionalität
```

### Option 3: Cloud Storage
```bash
# AWS S3, Google Cloud Storage, etc.
# Download-Script lädt von Cloud
```

---

**Erstellt**: 2025-10-10
**Autor**: ma3u
