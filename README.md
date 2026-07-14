# Öffentliche Webseite: Rechtliche Auseinandersetzung (EGMR-Beschwerde)

Diese Webseite dokumentiert die Menschenrechtsbeschwerde beim **Europäischen Gerichtshof für Menschenrechte (EGMR)** bezüglich des repressiven staatlichen Schulzwangs im Freistaat Sachsen ohne Qualitätskontrolle.

Die Seite ist zweisprachig (Deutsch / Englisch) aufgebaut und orientiert sich an dem [submodule-doc-pattern](https://github.com/henry1986/submodule-doc-pattern).

---

## 📂 Verzeichnisstruktur

* **`content/`**: Enthält die eigentlichen Markdown-Dateien der Zusatzschrift (Teil B) in Deutsch (`zusatzschrift_de.md`) und Englisch (`zusatzschrift_en.md`).
* **`template.html`**: Das HTML/CSS/JS-Layout-Template der Webseite.
* **`build.py`**: Zero-dependency Python-Skript, das die Markdown-Dateien parst und in das HTML-Template anstelle der Platzhalter einfügt.
* **`index.html`**: Die generierte deutsche Landingpage (Standard-Startseite).
* **`index_en.html`**: Die generierte englische Landingpage.
* **`.github/workflows/deploy.yml`**: Die GitHub Action für den automatischen Build und Deploy auf GitHub Pages bei jedem Push auf `main`.

---

## 🛠️ Lokaler Build

Wenn du Änderungen an `template.html` oder den Markdown-Dateien in `content/` vornimmst, kannst du die HTML-Seiten lokal wie folgt generieren:

```bash
python3 build.py
```

Anschließend kannst du die `index.html` oder `index_en.html` direkt im Webbrowser öffnen, um das Ergebnis zu betrachten.

---

## 🚀 Deployment

Das Deployment erfolgt vollautomatisch:
1. Nimm deine Änderungen an `content/` oder `template.html` vor.
2. Führe den lokalen Build aus, um sicherzustellen, dass keine Fehler auftreten.
3. Committe die Änderungen und pushe sie auf GitHub:
   ```bash
   git add .
   git commit -m "update content"
   git push origin main
   ```
4. Die GitHub Action baut die Seiten neu und veröffentlicht sie auf deiner GitHub Pages-Domain.
