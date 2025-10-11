# 🚀 QUICKSTART - Sozialrecht RAG Datenbank

Schnellstart-Anleitung zum Herunterladen und Nutzen der Sozialgesetzbuch-Datenbank.

## ✅ Was bereits heruntergeladen wurde

### Gesetze (100% komplett)
```bash
✅ SGB I-XIV: 13 Dateien, 8.8 MB
Pfad: Sozialrecht_RAG/Gesetze/
```

### Fachliche Weisungen (7.5% komplett)
```bash
🔄 SGB II: 6/~80 Dokumente
Pfad: Sozialrecht_RAG/Fachliche_Weisungen/SGB_II/
```

## 📥 Nächste Downloads

### 1. SGB II Fachliche Weisungen vervollständigen

Das Skript ist bereits vorbereitet:

```bash
cd /Users/ma3u/projects/sozialgesetze/Sozialrecht_RAG
./download_scripts/download_sgb2_fw.sh
```

**Dauer**: ~5-10 Minuten
**Größe**: ~120 MB
**Anzahl**: ~80 Dokumente

### 2. BMAS Rundschreiben SGB XII

Erstelle Download-Liste:
```bash
# URLs aus WebFetch-Ergebnissen extrahieren
cat > download_scripts/bmas_sgb12_urls.txt << 'EOF'
2024/01|§ 35|https://www.bmas.de/SharedDocs/Downloads/DE/Soziales/rundschreiben-2024-01.pdf
2023/01|§ 30|https://www.bmas.de/SharedDocs/Downloads/DE/Soziales/rundschreiben-2023-01.pdf
# ... weitere URLs
EOF

# Download ausführen
bash download_scripts/download_bmas_sgb12.sh
```

**Dauer**: ~2 Minuten
**Größe**: ~3 MB
**Anzahl**: 11 Dokumente

### 3. BMAS Rundschreiben SGB XIV

```bash
# Ähnliches Vorgehen wie SGB XII
bash download_scripts/download_bmas_sgb14.sh
```

**Dauer**: ~3 Minuten
**Größe**: ~5 MB
**Anzahl**: ~20 Dokumente

### 4. SGB III Fachliche Weisungen

```bash
bash download_scripts/download_sgb3_fw.sh
```

**Dauer**: ~8 Minuten
**Größe**: ~80 MB
**Anzahl**: ~50 Dokumente

### 5. SGB I Fachliche Weisungen

```bash
bash download_scripts/download_sgb1_fw.sh
```

**Dauer**: ~5 Minuten
**Größe**: ~40 MB
**Anzahl**: ~30 Dokumente

## 📊 Gesamtübersicht nach Vervollständigung

```
Kategorie                  | Dateien | Größe    | Status
---------------------------|---------|----------|--------
Gesetze (SGB I-XIV)        | 13      | 8.8 MB   | ✅ 100%
Fachliche Weisungen SGB II | ~80     | ~120 MB  | 🔄 7.5%
Fachliche Weisungen SGB III| ~50     | ~80 MB   | ⏳ 0%
Fachliche Weisungen SGB I  | ~30     | ~40 MB   | ⏳ 0%
BMAS Rundschreiben SGB XII | 11      | 3 MB     | ⏳ 0%
BMAS Rundschreiben SGB XIV | ~20     | 5 MB     | ⏳ 0%
---------------------------|---------|----------|--------
GESAMT                     | ~204    | ~257 MB  | 🔄 9%
```

## 🔧 Verfügbare Skripte

### Download-Skripte
```bash
download_scripts/
├── sgb2_fw_urls.txt           # SGB II Weisungen URL-Liste
├── download_sgb2_fw.sh        # ✅ Fertig
├── download_sgb3_fw.sh        # ⏳ Zu erstellen
├── download_sgb1_fw.sh        # ⏳ Zu erstellen
├── download_bmas_sgb12.sh     # ⏳ Zu erstellen
└── download_bmas_sgb14.sh     # ⏳ Zu erstellen
```

### Metadaten-Dateien
```bash
Metadaten/
├── Download_Log.txt           # ⏳ Automatisch generiert
├── Quellenverzeichnis.txt     # ✅ Komplett
├── Aktualisierungsdaten.txt   # ✅ Komplett
└── Update_Scheduler.txt       # ⏳ Zu erstellen
```

## 🚀 Vollständiger Download-Workflow

### Option 1: Schritt für Schritt (Empfohlen)
```bash
# 1. SGB II Weisungen
./download_scripts/download_sgb2_fw.sh

# 2. BMAS Rundschreiben
./download_scripts/download_bmas_sgb12.sh
./download_scripts/download_bmas_sgb14.sh

# 3. Weitere Weisungen
./download_scripts/download_sgb3_fw.sh
./download_scripts/download_sgb1_fw.sh

# 4. Validierung
bash validate_downloads.sh
```

**Gesamtdauer**: ~25-30 Minuten

### Option 2: Automatisiert (Master-Skript erstellen)
```bash
# Master-Download-Skript
cat > download_all.sh << 'EOF'
#!/bin/bash
echo "Starting complete download..."
./download_scripts/download_sgb2_fw.sh
./download_scripts/download_bmas_sgb12.sh
./download_scripts/download_bmas_sgb14.sh
./download_scripts/download_sgb3_fw.sh
./download_scripts/download_sgb1_fw.sh
echo "Download complete! Running validation..."
bash validate_downloads.sh
EOF

chmod +x download_all.sh
./download_all.sh
```

## 📝 Fehlgeschlagene Downloads beheben

### Einzelne URLs nachträglich herunterladen
```bash
# Prüfe Log für Fehler
grep "FAILED" Metadaten/download_log_sgb2_fw.txt

# Beispiel: § 7a manuell herunterladen
curl -L -o "Fachliche_Weisungen/SGB_II/FW_SGB_II_Par_07a_Leistungsberechtigung.pdf" \
  "https://www.arbeitsagentur.de/datei/fw-sgb-ii-7a_ba146798.pdf"
```

### Alternative Quellen nutzen
```bash
# Bei BA-Fehlern: Harald Thome als Fallback
curl -L -o "Fachliche_Weisungen/SGB_II/FW_SGB_II_Par_16.pdf" \
  "https://harald-thome.de/files/pdf/redakteur/BA_FH/FW%2016%20-%2026.03.2025.pdf"
```

## 🔍 Qualitätsprüfung

### Automatische Validierung
```bash
# Erstelle Validierungs-Skript
cat > validate_downloads.sh << 'EOF'
#!/bin/bash
echo "=== Validierung gestartet ==="

# PDF-Integrität prüfen
for pdf in Gesetze/*.pdf Fachliche_Weisungen/*/*.pdf; do
  if pdfinfo "$pdf" >/dev/null 2>&1; then
    echo "✅ $pdf"
  else
    echo "❌ FEHLER: $pdf ist beschädigt!"
  fi
done

# Dateigrößen prüfen
find . -name "*.pdf" -size 0 -print | while read file; do
  echo "⚠️ WARNUNG: $file ist leer!"
done

echo "=== Validierung abgeschlossen ==="
EOF

chmod +x validate_downloads.sh
./validate_downloads.sh
```

### Manuelle Stichproben
```bash
# Öffne zufällige PDFs zur Sichtprüfung
open "$(ls Gesetze/*.pdf | shuf -n 1)"
open "$(ls Fachliche_Weisungen/SGB_II/*.pdf | shuf -n 1)"
```

## 📈 Fortschritt überwachen

### Echtzeit-Status
```bash
# Aktuelle Anzahl heruntergeladener Dateien
find . -name "*.pdf" | wc -l

# Gesamtgröße
du -sh Sozialrecht_RAG/

# Nach Kategorie
du -sh Gesetze/ Fachliche_Weisungen/ Rundschreiben_BMAS/
```

### Detaillierte Statistik
```bash
cat << 'EOF' > status.sh
#!/bin/bash
echo "=== Download-Status ==="
echo "Gesetze:           $(ls -1 Gesetze/*.pdf 2>/dev/null | wc -l)/13"
echo "SGB II Weisungen:  $(ls -1 Fachliche_Weisungen/SGB_II/*.pdf 2>/dev/null | wc -l)/80"
echo "SGB III Weisungen: $(ls -1 Fachliche_Weisungen/SGB_III/*.pdf 2>/dev/null | wc -l)/50"
echo "SGB I Weisungen:   $(ls -1 Fachliche_Weisungen/SGB_I/*.pdf 2>/dev/null | wc -l)/30"
echo "BMAS SGB XII:      $(ls -1 Rundschreiben_BMAS/SGB_XII_Grundsicherung/*.pdf 2>/dev/null | wc -l)/11"
echo "BMAS SGB XIV:      $(ls -1 Rundschreiben_BMAS/SGB_XIV_Soziale_Entschaedigung/*.pdf 2>/dev/null | wc -l)/20"
echo ""
echo "Gesamtgröße: $(du -sh . | cut -f1)"
EOF

chmod +x status.sh
./status.sh
```

## 🔄 Automatische Updates einrichten

### Cron-Job für wöchentliche Updates
```bash
# Crontab bearbeiten
crontab -e

# Hinzufügen:
# Jeden Montag um 9:00 Uhr
0 9 * * 1 cd /Users/ma3u/projects/sozialgesetze/Sozialrecht_RAG && ./update_weekly.sh

# update_weekly.sh erstellen
cat > update_weekly.sh << 'EOF'
#!/bin/bash
# Wöchentliche Aktualisierungsprüfung
./download_scripts/check_updates.sh
# Bei Änderungen: Automatischer Download
# Email-Benachrichtigung versenden
EOF

chmod +x update_weekly.sh
```

## 📚 RAG-Integration vorbereiten

### 1. PDF-Text-Extraktion
```bash
# Installiere pdfplumber
pip install pdfplumber pandas

# Extraktions-Skript
python extract_text.py
```

### 2. Chunking-Strategie
```python
# paragraph_chunker.py
import pdfplumber

def extract_paragraphs(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            # Paragraph-basierte Segmentierung
            paragraphs = text.split('\n\n')
            for p in paragraphs:
                if p.strip():
                    yield p.strip()
```

### 3. Embedding erstellen
```python
# embeddings.py
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
embeddings = model.encode(chunks)
```

## ❓ Häufige Probleme

### Problem: "404 Not Found"
**Lösung**: URL hat sich geändert
```bash
# Prüfe neue URL auf der Webseite
# Aktualisiere sgb2_fw_urls.txt
# Wiederhole Download
```

### Problem: "Connection timeout"
**Lösung**: Server überlastet
```bash
# Warte 5 Minuten
# Wiederhole mit erhöhtem Timeout:
curl --max-time 300 -L -o "file.pdf" "URL"
```

### Problem: "PDF ist beschädigt"
**Lösung**: Unvollständiger Download
```bash
# Lösche beschädigte Datei
rm "beschädigte_datei.pdf"
# Wiederhole Download
```

## 📞 Support

### Logs prüfen
```bash
# Download-Fehler
cat Metadaten/download_log_sgb2_fw.txt | grep FAILED

# Alle Logs
ls -lh Metadaten/*.txt
```

### Hilfreiche Befehle
```bash
# Alle PDFs auflisten
find . -name "*.pdf" -type f

# Duplikate finden
fdupes -r . | grep pdf

# Metadaten extrahieren
pdfinfo Gesetze/SGB_01_Allgemeiner_Teil.pdf
```

## ✅ Checkliste für vollständigen Download

- [ ] SGB I-XIV Gesetze (13 Dateien) ✅ Komplett
- [ ] SGB II Fachliche Weisungen (~80 Dateien) 🔄 7.5%
- [ ] SGB III Fachliche Weisungen (~50 Dateien) ⏳
- [ ] SGB I Fachliche Weisungen (~30 Dateien) ⏳
- [ ] BMAS Rundschreiben SGB XII (11 Dateien) ⏳
- [ ] BMAS Rundschreiben SGB XIV (~20 Dateien) ⏳
- [ ] Metadaten vollständig
- [ ] Validierung durchgeführt
- [ ] README.md gelesen
- [ ] Update-Mechanismus eingerichtet

---

**Status**: 🔄 In Arbeit (9% komplett)
**Nächster Schritt**: SGB II Weisungen vervollständigen
**Geschätzter Zeitaufwand bis Fertigstellung**: 30-40 Minuten

Bei Fragen siehe: README.md oder Quellenverzeichnis.txt
