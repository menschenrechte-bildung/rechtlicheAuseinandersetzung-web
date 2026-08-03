#!/usr/bin/env python3
import os
import re
import json

# Configuration
# Go to https://web3forms.com/ to get your free Access Key and paste it here:
WEB3FORMS_ACCESS_KEY = "51d5d6f8-351d-4f5c-ace8-341fee5619d0"

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
    
    # Load new biography content for DE
    if os.path.exists("content/biografie_de.md"):
        with open("content/biografie_de.md", "r", encoding="utf-8") as f:
            de_data["introduction"] = md_to_html(f.read())
            de_data["preliminary_remark"] = ""

    if os.path.exists("content/gedanken_de.md"):
        with open("content/gedanken_de.md", "r", encoding="utf-8") as f:
            de_gedanken_html = md_to_html(f.read())
            # Put gedanken in facts for now or as single block
    
    if os.path.exists("content/dokumente_de.md"):
        with open("content/dokumente_de.md", "r", encoding="utf-8") as f:
            de_docs_html = md_to_html(f.read())

    
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
            "meta_title": "Schulweg außerhalb der Norm – Selbstbestimmte Bildung & EGMR-Beschwerde",
            "meta_desc": "Eine persönliche Geschichte über die Grenzen des staatlichen Schulzwangs, den Erfolg durch Selbststudium und die juristische Beschwerde beim EGMR.",
            "badge": "Bildungsgeschichte & Selbstbestimmung",
            "title": "Schulweg außerhalb der Norm",
            "subtitle": "Vom Leidensdruck im staatlichen System über den Erfolg im Selbststudium bis zur Beschwerde beim EGMR.",
            "tab_overview": "📖 Unsere Geschichte",
            "tab_facts": "💭 Gedanken & Blog",
            "tab_legal": "⚖️ EGMR-Beschwerde",
            "tab_documents": "📁 Dokumente & Beweise",
            "introduction_title": "Unsere Geschichte (Etappen)",
            "preliminary_title": "Das Dreiecksverhältnis und das systemische Rechtsvakuum",
            "timeline_title": "Gedanken & Systemkritik",
            "timeline_desc": "Hier hinterfragen wir etablierte Grundsätze des Schulsystems im Vergleich zu den Grundrechten von Erwachsenen.",
            "legal_title": "Rechtliche Rügen unter der EMRK",
            "legal_desc": "Die Beschwerde richtet sich nicht gegen die Schulpflicht an sich, sondern gegen das Fehlen von konventionsrechtlichen Mindestgarantien bei der staatlichen Zwangsverbüßung.",
            "documents_title": "Verzeichnis der Dokumente und Transkripte",
            "documents_desc": "Transkriptionen aller relevanten Urkunden, Bescheide und Gerichtsentscheidungen im Volltext.",
            "timeline_hint": "Klicke auf die Beiträge, um sie zu lesen:",
            "conclusion_title": "Schluss: Eine neuartige Frage zur Konvention und Anträge",
            "next_to_facts": "Weiter zu Gedanken & Blog",
            "next_to_legal": "Weiter zur EGMR-Beschwerde",
            "next_to_documents": "Weiter zu den Dokumenten",
            "back_to_overview": "Zurück zur Geschichte",
            "back_to_facts": "Zurück zu Gedanken & Blog",
            "back_to_legal": "Zurück zur EGMR-Beschwerde",
            "docs_contact_title": "Presseanfragen & Wissenschaftlicher Austausch",
            "docs_contact_text": "Journalisten, Wissenschaftler und juristische Fachkreise können hier eine Anfrage senden, um Zugang zu den ungeschwärzten Originalbelegen und Akten zu erhalten.",
            "form_label_name": "Name / Organisation",
            "form_label_email": "E-Mail-Adresse",
            "form_label_message": "Ihre Nachricht",
            "form_btn_send": "Anfrage senden",
            "form_sending_status": "Wird gesendet...",
            "form_success_message": "Vielen Dank! Ihre Anfrage wurde erfolgreich übermittelt.",
            "docs_top_notice_text": "Für Anfragen zum Zugang zu ungeschwärzten Originaldokumenten oder für wissenschaftlichen Austausch nutzen Sie bitte das",
            "docs_top_notice_link": "Kontaktformular am Ende dieser Seite",
            "hero_quote_text": "„Erst glaubten wir an das System. Dann forderten wir Gesetz und Lernfreude ein. Als der Staat mit Verweigerung reagierte, übernahmen wir selbst die Verantwortung – und machten den Weg frei für ein Leben in Selbstbestimmung: mit den besten Noten, die unser Sohn je hatte, und vor allem mit einem Kind, das wieder glücklich war.“",
            "hero_btn_story": "📖 Die ganze Story lesen",
            "hero_btn_docs": "📁 Beweise & Dokumente"
        },
        "en": {
            "meta_title": "A Journey Beyond Standard Schooling – Self-Study & ECHR Application",
            "meta_desc": "A personal journey highlighting the limits of compulsory schooling, success through self-study, and the human rights complaint to the ECHR.",
            "badge": "Educational Journey & Autonomy",
            "title": "A Journey Beyond Standard Schooling",
            "subtitle": "From systemic pressure in public school to success in self-directed learning and our ECHR application.",
            "tab_overview": "📖 Our Story",
            "tab_facts": "💭 Reflections & Blog",
            "tab_legal": "⚖️ ECHR Application",
            "tab_documents": "📁 Documents & Evidence",
            "introduction_title": "Our Story (Milestones)",
            "preliminary_title": "The Tripartite Relationship and the Systemic Rights Vacuum",
            "timeline_title": "Reflections & Systemic Critique",
            "timeline_desc": "Questioning core assumptions of compulsory schooling compared to adult rights.",
            "legal_title": "Legal Arguments under the Convention",
            "legal_desc": "The complaints do not challenge compulsory schooling as such, but rather the lack of minimum safeguards when enforced through State coercion.",
            "documents_title": "Index of Documents and Transcripts",
            "documents_desc": "Full-text transcripts of all relevant decisions, notices, and court records.",
            "timeline_hint": "Click on articles to read:",
            "conclusion_title": "Conclusion: A Novel Convention Question and Relief Sought",
            "next_to_facts": "Next to Reflections & Blog",
            "next_to_legal": "Next to ECHR Application",
            "next_to_documents": "Next to Documents",
            "back_to_overview": "Back to Story",
            "back_to_facts": "Back to Reflections",
            "back_to_legal": "Back to ECHR Application",
            "docs_contact_title": "Press Enquiries & Academic Exchange",
            "docs_contact_text": "Journalists, legal scholars, and researchers may request access to unredacted original case files here.",
            "form_label_name": "Name / Organisation",
            "form_label_email": "Email Address",
            "form_label_message": "Your Message",
            "form_btn_send": "Send Enquiry",
            "form_sending_status": "Sending...",
            "form_success_message": "Thank you! Your enquiry has been submitted successfully.",
            "docs_top_notice_text": "For access to unredacted original case files or academic exchange, please use the",
            "docs_top_notice_link": "contact form at the bottom of this page",
            "hero_quote_text": "“At first, we believed in the system. Then we demanded compliance with the law and the preservation of learning joy. When the State responded with refusal, we took responsibility into our own hands – paving the way for a life of self-determination: with the best grades our son ever had, and above all, with a child who was happy again.”",
            "hero_btn_story": "📖 Read Our Story",
            "hero_btn_docs": "📁 Evidence & Documents"
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
            <span class="doc-category">Analysen</span>
            <h4>Entwicklungs- und Leistungsanalyse</h4>
            <p>Detaillierte Gegenüberstellung und Analyse der Leistungsentwicklung von Klasse 7 bis zum Abschluss 2026 (geschwärzt).</p>
            <div class="doc-actions">
                <a href="https://github.com/henry1986/rechtlicheAuseinandersetzung-web/blob/main/content/zeugnisvergleich_entwicklung.md" target="_blank" class="doc-btn">GitHub-Ansicht</a>
                <a href="content/zeugnisvergleich_entwicklung.md" target="_blank" class="doc-btn secondary">Rohdatei (.md)</a>
            </div>
        </div>
        <div class="doc-item-card">
            <span class="doc-category">Beweismittel</span>
            <h4>Jahreszeugnis Klasse 7b (2022/2023)</h4>
            <p>Zeugnis der 25. Oberschule Dresden vor dem Leistungseinbruch (Notenschnitt 3,91, Versetzung in den Hauptschulzweig, geschwärzt).</p>
            <div class="doc-actions">
                <a href="https://github.com/henry1986/rechtlicheAuseinandersetzung-web/blob/main/content/zeugnis_klasse_7b.md" target="_blank" class="doc-btn">GitHub-Ansicht</a>
                <a href="content/zeugnis_klasse_7b.md" target="_blank" class="doc-btn secondary">Rohdatei (.md)</a>
            </div>
        </div>
        <div class="doc-item-card">
            <span class="doc-category">Beweismittel</span>
            <h4>Jahreszeugnis Klasse 8b (2023/2024)</h4>
            <p>Zeugnis der 25. Oberschule Dresden nach Beginn der Abwesenheit (96 unentschuldigte Fehltage, formale Versetzung nach § 29 SOOSA, geschwärzt).</p>
            <div class="doc-actions">
                <a href="https://github.com/henry1986/rechtlicheAuseinandersetzung-web/blob/main/content/zeugnis_klasse_8b.md" target="_blank" class="doc-btn">GitHub-Ansicht</a>
                <a href="content/zeugnis_klasse_8b.md" target="_blank" class="doc-btn secondary">Rohdatei (.md)</a>
            </div>
        </div>
        <div class="doc-item-card">
            <span class="doc-category">Beweismittel</span>
            <h4>Abschlusszeugnis (Realschulabschluss)</h4>
            <p>Das am 26.06.2026 in Regelzeit bestandene Zeugnis der staatlichen Schulfremdenprüfung (Notenschnitt 2,71, geschwärzt).</p>
            <div class="doc-actions">
                <a href="https://github.com/henry1986/rechtlicheAuseinandersetzung-web/blob/main/content/zeugnis_realschulabschluss.md" target="_blank" class="doc-btn">GitHub-Ansicht</a>
                <a href="content/zeugnis_realschulabschluss.md" target="_blank" class="doc-btn secondary">Rohdatei (.md)</a>
            </div>
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
        <div class="doc-item-card">
            <span class="doc-category">Gerichtsentscheidungen</span>
            <h4>Nichtannahmebeschluss des BVerfG (1 BvR 242/26)</h4>
            <p>Der Beschluss der 2. Kammer des Ersten Senats vom 23. März 2026 zur Verfassungsbeschwerde.</p>
            <div style="font-size: 0.8rem; color: var(--text-muted); font-style: italic; margin-top: auto;">Details in der Chronologie (Abschnitt F) enthalten.</div>
        </div>
        <div class="doc-item-card">
            <span class="doc-category">Behördenakten</span>
            <h4>Akte Berufsschulpflichtüberwachung</h4>
            <p>Die Akte der Stadt Dresden ab Februar 2026 bezüglich der Androhung von 25.000 EUR Zwangsgeld oder Ersatzwangshaft.</p>
            <div style="font-size: 0.8rem; color: var(--text-muted); font-style: italic; margin-top: auto;">Details in der Chronologie (Abschnitt G) enthalten.</div>
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
            <span class="doc-category">Analyses</span>
            <h4>Development & Performance Analysis</h4>
            <p>Comparison and detailed analysis of academic performance development from Class 7 to the 2026 graduation (redacted, German).</p>
            <div class="doc-actions">
                <a href="https://github.com/henry1986/rechtlicheAuseinandersetzung-web/blob/main/content/zeugnisvergleich_entwicklung.md" target="_blank" class="doc-btn">GitHub-View</a>
                <a href="content/zeugnisvergleich_entwicklung.md" target="_blank" class="doc-btn secondary">Raw Markdown (.md)</a>
            </div>
        </div>
        <div class="doc-item-card">
            <span class="doc-category">Evidence</span>
            <h4>Annual Report Card Class 7b (2022/2023)</h4>
            <p>Report card from the 25th Secondary School Dresden prior to performance collapse (GPA 3.91, demotion to Hauptschul-track, redacted, German).</p>
            <div class="doc-actions">
                <a href="https://github.com/henry1986/rechtlicheAuseinandersetzung-web/blob/main/content/zeugnis_klasse_7b.md" target="_blank" class="doc-btn">GitHub-View</a>
                <a href="content/zeugnis_klasse_7b.md" target="_blank" class="doc-btn secondary">Raw Markdown (.md)</a>
            </div>
        </div>
        <div class="doc-item-card">
            <span class="doc-category">Evidence</span>
            <h4>Annual Report Card Class 8b (2023/2024)</h4>
            <p>Report card from the 25th Secondary School Dresden after school absence began, showing 96 unexcused absences (GPA 5.23, redacted, German).</p>
            <div class="doc-actions">
                <a href="https://github.com/henry1986/rechtlicheAuseinandersetzung-web/blob/main/content/zeugnis_klasse_8b.md" target="_blank" class="doc-btn">GitHub-View</a>
                <a href="content/zeugnis_klasse_8b.md" target="_blank" class="doc-btn secondary">Raw Markdown (.md)</a>
            </div>
        </div>
        <div class="doc-item-card">
            <span class="doc-category">Evidence</span>
            <h4>Graduation Certificate (Realschulabschluss)</h4>
            <p>State certificate successfully obtained on June 26, 2026, within regular school time (GPA 2.71, redacted, German).</p>
            <div class="doc-actions">
                <a href="https://github.com/henry1986/rechtlicheAuseinandersetzung-web/blob/main/content/zeugnis_realschulabschluss.md" target="_blank" class="doc-btn">GitHub-View</a>
                <a href="content/zeugnis_realschulabschluss.md" target="_blank" class="doc-btn secondary">Raw Markdown (.md)</a>
            </div>
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
        <div class="doc-item-card">
            <span class="doc-category">Court Records</span>
            <h4>Federal Constitutional Court Decision (1 BvR 242/26)</h4>
            <p>The final domestic decision by the Federal Constitutional Court rejecting the complaint without reasoning.</p>
            <div style="font-size: 0.8rem; color: var(--text-muted); font-style: italic; margin-top: auto;">Details included in the timeline (Milestone F).</div>
        </div>
        <div class="doc-item-card">
            <span class="doc-category">Administrative Records</span>
            <h4>Vocational School Monitoring & Coercion Case File</h4>
            <p>The Dresden administration file threatening EUR 25,000 in coercive fines or detention.</p>
            <div style="font-size: 0.8rem; color: var(--text-muted); font-style: italic; margin-top: auto;">Details included in the timeline (Milestone G).</div>
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
        output = output.replace("YOUR_ACCESS_KEY_HERE", WEB3FORMS_ACCESS_KEY)
        
        # Timeline inject
        output = output.replace("{{facts_timeline_json}}", timeline_json)
        
        # Legal Inject
        output = output.replace("{{legal_arguments_html}}", legal_arguments_html)
        
        # Documents Inject
        if lang == "de" and 'de_docs_html' in locals():
            output = output.replace("{{documents_content}}", de_docs_html)
        else:
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

    # Automatisches Verschlüsseln der generierten HTML-Dateien
    ENABLE_ENCRYPTION = True
    if ENABLE_ENCRYPTION:
        print("Running encryption step...")
        os.system("node encrypt.js")
    else:
        print("Encryption step skipped (ENABLE_ENCRYPTION = False).")

if __name__ == "__main__":
    build()


