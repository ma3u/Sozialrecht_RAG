# KRITISCHE BEFUNDE - Fehlende Aktualisierungen

**Erstellt**: 2025-10-10  
**Status**: KRITISCH ⚠️

---

## 🚨 HAUPTBEFUND: BA WEISUNGEN NICHT AKTUALISIERT!

### Problem
Die Bundesagentur für Arbeit hat **keine Fachlichen Weisungen** für die Regelbedarfs-Erhöhungen 2024/2025 veröffentlicht!

### Betroffene Dokumente

#### 1. SGB II § 20 (Regelbedarfe)
**Neueste verfügbare Version**: 27.11.2023  
**Quellen geprüft**:
- ✅ arbeitsagentur.de (ba034455) → November 2023
- ✅ harald-thome.de → November 2023
- ❌ Keine Version 2024 oder 2025 gefunden

**Fehlendes Update**:
- Regelbedarfe 2024 (Erhöhung ~12%)
- Regelbedarfe 2025 (Erhöhung ~3%)

**Aktuelle Beträge** (Stand 01.01.2025 laut Gesetz):
- Alleinstehende: 563 € (war 502 € in 2023 = +12%)
- Paare je: 506 €
- Jugendliche 14-17: 471 €
- Kinder 6-13: 390 €
- Kinder 0-5: 357 €

**Quelle für aktuelle Beträge**: SGB II § 20 Gesetz (gesetze-im-internet.de)

---

#### 2. SGB II § 19 (Bürgergeld)
**Neueste verfügbare Version**: 01.01.2023  
**Quellen geprüft**:
- ✅ arbeitsagentur.de → Nicht gefunden/veraltet
- ✅ harald-thome.de → Januar 2023
- ❌ Keine neuere Version verfügbar

**Problem**: Einführungs-Weisung von 2023, keine Aktualisierungen seit 2 Jahren

---

#### 3. SGB VI (Rentenversicherung)
**Neueste verfügbare Version**: 20.11.2017
**Quellen geprüft**:
- ✅ arbeitsagentur.de → Nur ALG2-Empfänger (spezifisch)
- ✅ harald-thome.de → November 2017
- ❌ DRV GRA → Kein einfaches PDF-Download-System

**Problem**: 8 Jahre alt, Grundrenten-Gesetz 2021 fehlt komplett!

---

## 💡 INTERPRETATION

### Warum fehlen die Updates?

**Mögliche Gründe**:

1. **Regelbedarfe stehen im Gesetz**
   - § 20 SGB II im Gesetzestext enthält die aktuellen Beträge
   - BA-Weisung erklärt nur die ANWENDUNG, nicht die Beträge
   - → Fachliche Weisung muss nicht bei jeder Betragsanpassung aktualisiert werden

2. **Fokus auf Gesetzesänderungen**
   - BA aktualisiert Weisungen nur bei SYSTEMATISCHEN Änderungen
   - Reine Betragsanpassungen → Gesetz nachlesen
   - → Weisung von 2023 erklärt das VERFAHREN (noch gültig)

3. **Verzögerung bei Veröffentlichung**
   - Möglich dass 2025er Weisungen noch in Erstellung sind
   - Aber: Unwahrscheinlich 10 Monate nach Jahresbeginn

---

## ✅ LÖSUNG FÜR RAG-SYSTEM

### Hybride Strategie:

#### Für BETRÄGE (Regelbedarfe, Freibeträge, etc.):
```
1. PRIMÄR: Gesetz lesen (SGB II § 20 von gesetze-im-internet.de)
2. SEKUNDÄR: Fachliche Weisung für VERFAHREN (Nov 2023)
```

**RAG-Prompt-Strategie**:
```python
if anfrage_nach_betraegen:
    quelle_1 = "SGB II § 20 Gesetz (gesetze-im-internet.de)"  # Aktuelle Beträge
    quelle_2 = "FW § 20 Nov 2023 (Verfahren)"  # Anwendungshinweise
    
    antwort = f"""
    Regelbedarfe 2025 (Stand: Gesetz):
    - Alleinstehende: 563 €
    - Paare je: 506 €
    
    Quelle Beträge: SGB II § 20 Gesetzestext (Stand: 01.01.2025)
    Quelle Verfahren: Fachliche Weisung BA (Stand: 27.11.2023)
    
    ⚠️ Hinweis: Beträge aus Gesetz, Verfahren aus Weisung.
    """
else:
    # Nur Fachliche Weisung nutzen
    pass
```

---

#### Für VERFAHRENSFRAGEN (Anwendung, Berechnung, etc.):
```
→ Fachliche Weisung Nov 2023 KANN verwendet werden
→ Verfahren hat sich wahrscheinlich nicht geändert
→ Aber: Immer Disclaimer mit Stand-Datum!
```

---

## 📋 FINALE EMPFEHLUNG FÜR DIE 3 KRITISCHEN DOKUMENTE

### 1. SGB VI (2017)
**Status**: 🔴 **NICHT LÖSBAR mit öffentlichen Quellen**

**Grund**:
- Keine neuere allgemeine RV-Weisung öffentlich verfügbar
- DRV hat keine einfachen PDF-Downloads
- BA hat nur ALG2-spezifische Weisungen

**RAG-Strategie**:
```
→ SGB VI GESETZ verwenden (aktuell!)
→ BA-Weisung ALG2-RV verwenden (spezifisch, neuergültig)
→ Alte allgemeine RV-Weisung ENTFERNEN
→ Disclaimer: "Für RV-Details bitte DRV konsultieren"
```

**Aktion**: Alte Datei löschen, Gesetz als Primärquelle nutzen

---

### 2. SGB II § 20 (Regelbedarfe)
**Status**: ⚠️ **TEILWEISE LÖSBAR**

**Verfügbar**: Nov 2023 (neueste Weisung)
**Problem**: Keine Weisung für 2024/2025 Beträge

**RAG-Strategie**:
```
Beträge:   → SGB II § 20 GESETZ (aktuell: 563€)
Verfahren: → Fachliche Weisung Nov 2023 (Anwendung)

Antwort kombinieren:
"Regelbedarf 2025: 563€ (Quelle: Gesetz)
Berechnungsverfahren siehe Fachliche Weisung (Stand: Nov 2023)"
```

**Aktion**: Behalten + Gesetz als Primärquelle

---

### 3. SGB II § 19 (Bürgergeld)
**Status**: ⚠️ **TEILWEISE LÖSBAR**

**Verfügbar**: Jan 2023 (Einführungs-Weisung)
**Problem**: Keine Aktualisierung für 2024/2025

**RAG-Strategie**:
```
→ Weisung 2023 für SYSTEMATIK (noch gültig)
→ Gesetz für aktuelle BETRÄGE
→ Disclaimer erforderlich
```

**Aktion**: Behalten + Gesetz als Primärquelle

---

## 🎯 FINALE HANDLUNGSANWEISUNGEN

### Sofortmaßnahmen (umgesetzt):
1. ✅ Alte SGB VI Weisung (2017) behalten aber als VERALTET markieren
2. ✅ SGB II § 20/19 Weisungen (2023) behalten
3. ✅ IMMER Gesetz als Primärquelle für Beträge nutzen

### RAG-Implementierung:
```python
def get_regelbedarf_info(anfrage):
    # HYBRID-Strategie
    
    # 1. Aktuelle Beträge aus GESETZ
    gesetz = load_sgb("SGB_02_Buergergeld.pdf")
    paragraph_20 = extract_paragraph(gesetz, "§ 20")
    
    # 2. Verfahrenshinweise aus WEISUNG
    weisung = load_fw("FW_SGB_II_Par_20_Regelbedarfe.pdf")
    
    # 3. Kombiniere mit Disclaimer
    antwort = f"""
    Regelbedarfe 2025:
    {extract_betraege(paragraph_20)}
    
    Berechnungsverfahren:
    {extract_verfahren(weisung)}
    
    Quellen:
    - Beträge: SGB II § 20 Gesetz (Stand: 01.01.2025) ⭐ Aktuell
    - Verfahren: Fachliche Weisung BA (Stand: 27.11.2023) ⚠️ Veraltet für Beträge
    
    Hinweis: Bei Widersprüchen gilt das Gesetz.
    """
    return antwort
```

---

## ✨ FAZIT

**Verfügbarkeit aktueller Versionen**:
- SGB VI ≥2024: ❌ Nicht öffentlich verfügbar
- SGB II § 20 2024/2025: ❌ BA hat nicht aktualisiert
- SGB II § 19 2024/2025: ❌ BA hat nicht aktualisiert

**ABER**: Problem ist lösbar durch **Hybrid-Strategie**:
→ Gesetz für Beträge + Weisung für Verfahren

**Für RAG-System**: ✅ Nutzbar mit korrekter Implementierung
**Ohne Hybrid-Strategie**: 🔴 Falschinformationen möglich!

---

**Empfehlung**: Hybrid-Ansatz implementieren + klare Disclaimer  
**Datei behalten**: Ja (mit Aktualitätswarnung in Metadaten)  
**Produktionsbereit**: ✅ Ja, mit Hybrid-Strategie

