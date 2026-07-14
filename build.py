#!/usr/bin/env python3
import os
import re
import json

def md_to_html(md_text):
    if not md_text:
        return ""
    
    # Process line-by-line
    lines = md_text.split('\n')
    html_parts = []
    
    in_list = False
    in_ordered_list = False
    in_quote = False
    quote_type = None
    quote_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # Close quote if line doesn't start with >
        if in_quote and not line.startswith('>'):
            quote_content = md_to_html('\n'.join(quote_lines))
            alert_class = f"alert alert-{quote_type.lower()}" if quote_type else "blockquote"
            html_parts.append(f'<div class="{alert_class}">{quote_content}</div>')
            in_quote = False
            quote_lines = []
            quote_type = None
            
        # Close list if line doesn't start with a list indicator
        if in_list and not (stripped.startswith('-') or stripped.startswith('*') or re.match(r'^\d+\.', stripped)):
            html_parts.append('</ul>' if not in_ordered_list else '</ol>')
            in_list = False
            in_ordered_list = False
            
        if not stripped:
            continue
            
        # Headers
        if line.startswith('#### '):
            html_parts.append(f'<h4>{stripped[5:]}</h4>')
        elif line.startswith('### '):
            html_parts.append(f'<h3>{stripped[4:]}</h3>')
        elif line.startswith('## '):
            html_parts.append(f'<h2>{stripped[3:]}</h2>')
        elif line.startswith('# '):
            html_parts.append(f'<h1>{stripped[2:]}</h1>')
        elif line == '---':
            html_parts.append('<hr class="divider"/>')
            
        # Blockquotes & Alerts
        elif line.startswith('>'):
            if not in_quote:
                in_quote = True
                # Check for GitHub-style alerts like > [!NOTE]
                match = re.match(r'^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]', line)
                if match:
                    quote_type = match.group(1)
                    continue
            content_line = re.sub(r'^>\s*', '', line)
            quote_lines.append(content_line)
            
        # Lists
        elif stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list:
                html_parts.append('<ul>')
                in_list = True
            item_text = stripped[2:]
            html_parts.append(f'<li>{item_text}</li>')
        elif re.match(r'^\d+\.\s', stripped):
            if not in_list:
                html_parts.append('<ol>')
                in_list = True
                in_ordered_list = True
            item_text = re.sub(r'^\d+\.\s*', '', stripped)
            html_parts.append(f'<li>{item_text}</li>')
            
        # Standard Paragraph
        else:
            html_parts.append(f'<p>{stripped}</p>')
            
    # Flush remaining quote/list
    if in_quote:
        quote_content = md_to_html('\n'.join(quote_lines))
        alert_class = f"alert alert-{quote_type.lower()}" if quote_type else "blockquote"
        html_parts.append(f'<div class="{alert_class}">{quote_content}</div>')
    if in_list:
        html_parts.append('</ul>' if not in_ordered_list else '</ol>')
        
    combined = '\n'.join(html_parts)
    
    # Inline formatting: bold, italic, links
    combined = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', combined)
    combined = re.sub(r'\*(.*?)\*', r'<em>\1</em>', combined)
    # Links [text](url) -> target="_blank"
    combined = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank">\1</a>', combined)
    
    return combined

def parse_zusatzschrift(filepath):
    """
    Parses the ECHR Zusatzschrift Markdown file into structured sections:
    - introduction
    - preliminary_remark
    - facts (milestones A-G)
    - legal_arguments (intro, dogmatic_framework, specific_violations)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
        
    sections = {}
    
    # Split the document by main headings "## "
    pattern = r'^##\s+(.+?)$'
    matches = list(re.finditer(pattern, text, re.MULTILINE))
    
    for i in range(len(matches)):
        start = matches[i].end()
        end = matches[i+1].start() if i + 1 < len(matches) else len(text)
        
        heading = matches[i].group(1).strip()
        content = text[start:end].strip()
        
        heading_upper = heading.upper()
        if "INTRODUCTION" in heading_upper or "EINLEITUNG" in heading_upper:
            sections["introduction"] = md_to_html(content)
        elif "PRELIMINARY REMARK" in heading_upper or "VORBEMERKUNG" in heading_upper:
            sections["preliminary_remark"] = md_to_html(content)
        elif "FACTS" in heading_upper or "SACHVERHALTS" in heading_upper:
            sections["facts"] = parse_facts_subsections(content)
        elif "LEGAL ARGUMENTS" in heading_upper or "RECHTLICHE BEGRÜNDUNG" in heading_upper:
            sections["legal_arguments"] = parse_legal_subsections(content)
        elif "CONCLUSION" in heading_upper or "SCHLUSS" in heading_upper:
            sections["conclusion"] = md_to_html(content)
            
    return sections

def parse_facts_subsections(facts_content):
    """
    Splits the facts content by "### " into milestones A to G
    """
    pattern = r'^###\s+(.+?)$'
    matches = list(re.finditer(pattern, facts_content, re.MULTILINE))
    
    subsections = []
    
    if not matches:
        return [{"title": "Facts", "content": md_to_html(facts_content), "id": "facts-general"}]
        
    for i in range(len(matches)):
        start = matches[i].end()
        end = matches[i+1].start() if i + 1 < len(matches) else len(facts_content)
        
        heading = matches[i].group(1).strip()
        content = facts_content[start:end].strip()
        
        letter_match = re.match(r'^([A-G])\.\s*(.+)$', heading)
        if letter_match:
            key = letter_match.group(1)
            title = letter_match.group(2)
        else:
            key = f"step_{i+1}"
            title = heading
            
        subsections.append({
            "id": key,
            "title": title,
            "content": md_to_html(content)
        })
        
    return subsections

def parse_legal_subsections(legal_content):
    """
    Parses the legal arguments into structured parts.
    """
    first_sub = re.search(r'^###\s+', legal_content, re.MULTILINE)
    intro_html = ""
    rest = legal_content
    
    if first_sub:
        intro_html = md_to_html(legal_content[:first_sub.start()].strip())
        rest = legal_content[first_sub.start():]
        
    pattern = r'^###\s+(.+?)$'
    matches = list(re.finditer(pattern, rest, re.MULTILINE))
    
    dogmatic_html = ""
    violations_html = ""
    violations_list = []
    
    for i in range(len(matches)):
        start = matches[i].end()
        end = matches[i+1].start() if i + 1 < len(matches) else len(rest)
        
        heading = matches[i].group(1).strip()
        content = rest[start:end].strip()
        
        heading_upper = heading.upper()
        if "DOGMATIC" in heading_upper or "DOGMATISCHE" in heading_upper:
            dogmatic_html = f"<h3>{heading}</h3>" + md_to_html(content)
        elif "SPECIFIC VIOLATIONS" in heading_upper or "SPEZIFISCHE VERLETZUNGEN" in heading_upper:
            violations_html = f"<h3>{heading}</h3>"
            violations_list = parse_specific_violations(content)
            
    return {
        "intro": intro_html,
        "dogmatic": dogmatic_html,
        "violations_header": violations_html,
        "violations": violations_list
    }

def parse_specific_violations(violations_content):
    """
    Splits the specific violations by "#### " into individual ECHR articles
    """
    pattern = r'^####\s+(.+?)$'
    matches = list(re.finditer(pattern, violations_content, re.MULTILINE))
    
    violations = []
    
    if not matches:
        return [{"title": "Violations", "content": md_to_html(violations_content)}]
        
    for i in range(len(matches)):
        start = matches[i].end()
        end = matches[i+1].start() if i + 1 < len(matches) else len(violations_content)
        
        heading = matches[i].group(1).strip()
        content = violations_content[start:end].strip()
        
        violations.append({
            "id": f"violation_{i+1}",
            "title": heading,
            "content": md_to_html(content)
        })
        
    return violations

def build():
    # Parse the documents
    print("Parsing German statement...")
    de_data = parse_zusatzschrift("content/zusatzschrift_de.md")
    print("Parsing English statement...")
    en_data = parse_zusatzschrift("content/zusatzschrift_en.md")
    
    # Load template
    with open("template.html", "r", encoding="utf-8") as f:
        template = f.read()
        
    # Build hreflangs block
    hreflangs_str = (
        '<link rel="alternate" hreflang="de" href="index.html" />\n    '
        '<link rel="alternate" hreflang="en" href="index_en.html" />\n    '
        '<link rel="alternate" hreflang="x-default" href="index.html" />'
    )
    
    # Set up translations dictionary
    translations = {
        "de": {
            "meta_title": "EGMR-Beschwerde: Martin & Lucas Heinrich ./. Deutschland",
            "meta_desc": "Dokumentation der Menschenrechtsbeschwerde beim EGMR gegen den repressiven Schulzwang in Sachsen ohne Qualitätssicherung.",
            "badge": "Menschenrechtsbeschwerde",
            "title": "Staatlicher Schulzwang?",
            "subtitle": "Nur mit gesetzlicher Qualitätskontrolle und kinderfreundlichen Rechtsbehelfen.",
            "tab_overview": "Übersicht",
            "tab_facts": "Chronologie",
            "tab_legal": "Rechtliche Rügen",
            "tab_documents": "Dokumente",
            "introduction_title": "Einleitung und Zweck dieser Zusatzschrift",
            "preliminary_title": "Das Dreiecksverhältnis und das systemische Rechtsvakuum",
            "timeline_title": "Chronologie der Ereignisse",
            "timeline_desc": "Vom pädagogischen Missstand an der Schule über den erworbenen Abschluss im Selbststudium bis hin zur existenzbedrohenden Zwangsgeldandrohung.",
            "legal_title": "Rechtliche Rügen unter der EMRK",
            "legal_desc": "Die Beschwerde richtet sich nicht gegen die Schulpflicht an sich, sondern gegen das Fehlen von konventionsrechtlichen Mindestgarantien bei der staatlichen Zwangsverbüßung.",
            "documents_title": "Verzeichnis der Dokumente und Transkripte",
            "documents_desc": "Transkriptionen aller relevanten Urkunden, Bescheide und Gerichtsentscheidungen im Volltext.",
            "timeline_hint": "Klicke auf die Milestones, um die Details anzuzeigen:",
            "conclusion_title": "Schluss: Eine neuartige Frage zur Konvention und Anträge",
            "next_to_facts": "Weiter zur Chronologie",
            "next_to_legal": "Weiter zur Begründung",
            "next_to_documents": "Weiter zu den Dokumenten",
            "back_to_overview": "Zurück zur Übersicht",
            "back_to_facts": "Zurück zur Chronologie",
            "back_to_legal": "Zurück zur Begründung"
        },
        "en": {
            "meta_title": "ECHR Application: Martin & Lucas Heinrich v. Germany",
            "meta_desc": "Documentation of the human rights complaint to the ECHR challenging compulsory school attendance in Saxony without quality assurance.",
            "badge": "ECHR Application",
            "title": "State School Coercion?",
            "subtitle": "Only with quality control and child-friendly remedies.",
            "tab_overview": "Overview",
            "tab_facts": "Timeline",
            "tab_legal": "Legal Violations",
            "tab_documents": "Documents",
            "introduction_title": "Introduction and Purpose of this Statement",
            "preliminary_title": "The Tripartite Relationship and the Systemic Rights Vacuum",
            "timeline_title": "Timeline of Events",
            "timeline_desc": "From pedagogical abuse in public school to self-study graduation in regular time, and ongoing coercive prosecution.",
            "legal_title": "Legal Arguments under the Convention",
            "legal_desc": "The complaints do not challenge compulsory schooling as such, but rather the lack of minimum safeguards when enforced through State coercion.",
            "documents_title": "Index of Documents and Transcripts",
            "documents_desc": "Full-text transcripts of all relevant decisions, notices, and court records.",
            "timeline_hint": "Click on the milestones to view the details:",
            "conclusion_title": "Conclusion: A Novel Convention Question and Relief Sought",
            "next_to_facts": "Next to Timeline",
            "next_to_legal": "Next to Legal Arguments",
            "next_to_documents": "Next to Documents",
            "back_to_overview": "Back to Overview",
            "back_to_facts": "Back to Timeline",
            "back_to_legal": "Back to Legal Arguments"
        }
    }
    
    # Document directory entries (DE and EN lists)
    documents_de = """
    <div class="docs-list">
        <div class="doc-item-card">
            <span class="doc-category">Hauptschriften</span>
            <h4>Zusatzschrift (Teil B) – Deutsch</h4>
            <p>Die ausführliche Begründung der Konventionsrügen (Artikel 2 ZP I, 8, 10, 6 und 13 EMRK).</p>
            <div class="doc-actions">
                <a href="https://github.com/henry1986/rechtlicheAuseinandersetzung-web/blob/main/content/zusatzschrift_de.md" target="_blank" class="doc-btn">GitHub-Ansicht</a>
                <a href="content/zusatzschrift_de.md" target="_blank" class="doc-btn secondary">Rohdatei (.md)</a>
            </div>
        </div>
        <div class="doc-item-card">
            <span class="doc-category">Gerichtsentscheidungen</span>
            <h4>Nichtannahmebeschluss des BVerfG (1 BvR 242/26)</h4>
            <p>Der Beschluss der 2. Kammer des Ersten Senats vom 23. März 2026 zur Verfassungsbeschwerde.</p>
            <div style="font-size: 0.8rem; color: var(--text-muted); font-style: italic; margin-top: auto;">Details in der Chronologie (Abschnitt F) enthalten.</div>
        </div>
        <div class="doc-item-card">
            <span class="doc-category">Beweismittel</span>
            <h4>Abschlusszeugnis (Realschulabschluss)</h4>
            <p>Das am 26.06.2026 erfolgreich in Regelzeit bestandene Zeugnis für Schulfremde (Durchschnitt 2,71).</p>
            <div style="font-size: 0.8rem; color: var(--text-muted); font-style: italic; margin-top: auto;">Details in der Chronologie (Abschnitt C) enthalten.</div>
        </div>
        <div class="doc-item-card">
            <span class="doc-category">Behördenakten</span>
            <h4>Akte Berufsschulpflichtüberwachung</h4>
            <p>Die Akte der Stadt Dresden ab Februar 2026 bezüglich der Androhung von 25.000 EUR Zwangsgeld oder Ersatzwangshaft.</p>
            <div style="font-size: 0.8rem; color: var(--text-muted); font-style: italic; margin-top: auto;">Details in der Chronologie (Abschnitt G) enthalten.</div>
        </div>
        <div class="doc-item-card">
            <span class="doc-category">Auskünfte</span>
            <h4>Bescheid des Sächsischen Kultusministeriums (SMK)</h4>
            <p>Offizieller Bescheid, der die Aussetzung aller externen Schulevaluationen in Sachsen seit 2015 belegt (redigiert).</p>
            <div class="doc-actions">
                <a href="https://github.com/henry1986/rechtlicheAuseinandersetzung-web/blob/main/content/transparenzbescheid_de.md" target="_blank" class="doc-btn">GitHub-Ansicht</a>
                <a href="content/transparenzbescheid_de.md" target="_blank" class="doc-btn secondary">Rohdatei (.md)</a>
            </div>
        </div>
    </div>
    """
    
    documents_en = """
    <div class="docs-list">
        <div class="doc-item-card">
            <span class="doc-category">Main Statements</span>
            <h4>Additional Statement (Part B) – English</h4>
            <p>The detailed human rights arguments challenging the German state actions under Articles 2 of Protocol 1, 8, 10, 6, and 13 ECHR.</p>
            <div class="doc-actions">
                <a href="https://github.com/henry1986/rechtlicheAuseinandersetzung-web/blob/main/content/zusatzschrift_en.md" target="_blank" class="doc-btn">GitHub-View</a>
                <a href="content/zusatzschrift_en.md" target="_blank" class="doc-btn secondary">Raw Markdown (.md)</a>
            </div>
        </div>
        <div class="doc-item-card">
            <span class="doc-category">Court Records</span>
            <h4>Federal Constitutional Court Decision (1 BvR 242/26)</h4>
            <p>The final domestic decision by the Federal Constitutional Court rejecting the complaint without reasoning.</p>
            <div style="font-size: 0.8rem; color: var(--text-muted); font-style: italic; margin-top: auto;">Details included in the timeline (Milestone F).</div>
        </div>
        <div class="doc-item-card">
            <span class="doc-category">Evidence</span>
            <h4>Graduation Certificate (Realschulabschluss)</h4>
            <p>The official state certificate successfully obtained on June 26, 2026, within regular school time (GPA 2.71).</p>
            <div style="font-size: 0.8rem; color: var(--text-muted); font-style: italic; margin-top: auto;">Details included in the timeline (Milestone C).</div>
        </div>
        <div class="doc-item-card">
            <span class="doc-category">Administrative Records</span>
            <h4>Vocational School Monitoring & Coercion Case File</h4>
            <p>The Dresden administration file threatening EUR 25,000 in coercive fines or detention.</p>
            <div style="font-size: 0.8rem; color: var(--text-muted); font-style: italic; margin-top: auto;">Details included in the timeline (Milestone G).</div>
        </div>
        <div class="doc-item-card">
            <span class="doc-category">Transparency disclosures</span>
            <h4>Ministry of Education Disclosure Decision</h4>
            <p>Official decision confirming the suspension of all external school quality evaluations in Saxony since 2015 (redacted, German).</p>
            <div class="doc-actions">
                <a href="https://github.com/henry1986/rechtlicheAuseinandersetzung-web/blob/main/content/transparenzbescheid_de.md" target="_blank" class="doc-btn">GitHub-View</a>
                <a href="content/transparenzbescheid_de.md" target="_blank" class="doc-btn secondary">Raw Markdown (.md)</a>
            </div>
        </div>
    </div>
    """
    
    # Process both languages
    for lang in ["de", "en"]:
        lang_trans = translations[lang]
        data = de_data if lang == "de" else en_data
        
        # Prepare facts timeline JSON and HTML navigation
        timeline_list = data["facts"]
        timeline_json = json.dumps(timeline_list, ensure_ascii=False, indent=8)
        
        # Build legal arguments HTML (accordions)
        legal_html_parts = []
        legal_html_parts.append(data["legal_arguments"]["intro"])
        legal_html_parts.append('<div class="dogmatic-section">')
        legal_html_parts.append(data["legal_arguments"]["dogmatic"])
        legal_html_parts.append('</div>')
        
        legal_html_parts.append(data["legal_arguments"]["violations_header"])
        legal_html_parts.append('<div class="accordions-container">')
        for viol in data["legal_arguments"]["violations"]:
            legal_html_parts.append(f"""
            <div class="accordion-item" id="{viol["id"]}">
                <button class="accordion-trigger" onclick="toggleAccordion('{viol["id"]}')">
                    <span class="accordion-title">{viol["title"]}</span>
                    <span class="accordion-icon">
                        <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"></path>
                        </svg>
                    </span>
                </button>
                <div class="accordion-content">
                    <div class="accordion-inner">
                        {viol["content"]}
                    </div>
                </div>
            </div>
            """)
        legal_html_parts.append('</div>')
        legal_arguments_html = '\n'.join(legal_html_parts)
        
        # Replaces in template
        output = template
        output = output.replace("{{lang}}", lang)
        output = output.replace("{{hreflangs}}", hreflangs_str)
        output = output.replace("{{giscus_lang}}", "de" if lang == "de" else "en")
        
        # Timeline inject
        output = output.replace("{{facts_timeline_json}}", timeline_json)
        
        # Legal Inject
        output = output.replace("{{legal_arguments_html}}", legal_arguments_html)
        
        # Documents Inject
        output = output.replace("{{documents_content}}", documents_de if lang == "de" else documents_en)
        
        # Replace basic translation keys
        for key, val in lang_trans.items():
            output = output.replace(f"{{{{{key}}}}}", val)
            
        # Parse inline templates
        output = output.replace("{{introduction_content}}", data["introduction"])
        output = output.replace("{{preliminary_remark_content}}", data["preliminary_remark"])
        output = output.replace("{{conclusion_content}}", data.get("conclusion", ""))
        
        # Write file
        filename = "index.html" if lang == "de" else f"index_{lang}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(output)
            
        print(f"Generated {filename} ({lang})")

if __name__ == "__main__":
    build()
