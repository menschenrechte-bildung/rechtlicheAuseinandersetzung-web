const { execSync } = require('child_process');
const fs = require('fs');

const WEB3FORMS_ACCESS_KEY = "51d5d6f8-351d-4f5c-ace8-341fee5619d0";

const contactFormHtml = `
<div style="margin-top: 2rem; border-top: 1px solid var(--gray-700); padding-top: 1.5rem; text-align: left;">
    <p style="font-size: 0.9rem; color: #a1a1aa; margin-bottom: 1rem; text-align: center;">
        Sie haben noch kein Passwort? Fordern Sie den Zugangsschlüssel einfach an:
    </p>
    <form action="https://api.web3forms.com/submit" method="POST" style="display: flex; flex-direction: column; gap: 0.75rem;">
        <input type="hidden" name="access_key" value="${WEB3FORMS_ACCESS_KEY}">
        <input type="hidden" name="subject" value="Passwort-Anfrage - Rechtliche Auseinandersetzung">
        <input type="checkbox" name="botcheck" style="display: none;">

        <input type="text" name="name" required placeholder="Ihr Name" style="background: var(--gray-800); border: 1px solid var(--gray-700); padding: 0.5rem 0.75rem; border-radius: 0.25rem; color: #fff; font-size: 0.875rem; outline: none;">
        <input type="email" name="email" required placeholder="Ihre E-Mail-Adresse" style="background: var(--gray-800); border: 1px solid var(--gray-700); padding: 0.5rem 0.75rem; border-radius: 0.25rem; color: #fff; font-size: 0.875rem; outline: none;">
        <textarea name="message" rows="2" placeholder="Kurze Nachricht (optional)" style="background: var(--gray-800); border: 1px solid var(--gray-700); padding: 0.5rem 0.75rem; border-radius: 0.25rem; color: #fff; font-size: 0.875rem; outline: none; resize: vertical;"></textarea>

        <button type="submit" style="background: #6366f1; color: #fff; border: none; padding: 0.5rem; border-radius: 0.25rem; font-weight: 600; cursor: pointer; font-size: 0.875rem; margin-top: 0.25rem;">Passwort anfordern</button>
        
        <p style="font-size: 0.75rem; color: #71717a; margin-top: 0.5rem; line-height: 1.4;">
            <strong>Datenschutzhinweis:</strong> Die eingegebenen Daten (Name, E-Mail) werden ausschließlich zur Bearbeitung und Beantwortung Ihrer Passwort-Anfrage genutzt. Eine Weitergabe an Dritte erfolgt nicht. Die Kommunikation wird im Rahmen üblicher E-Mail-Aufbewahrung gespeichert.
        </p>
    </form>
</div>
`;

function encryptFile(file, password) {
    console.log(`Verschlüssele ${file}...`);
    // npx pagecrypt aufrufen
    execSync(`npx pagecrypt ${file} ${file} "${password}"`, { stdio: 'inherit' });
    
    // Nachbearbeiten: Groß-/Kleinschreibung beim Passwort ignorieren & Kontaktformular auf Sperrbildschirm einfügen
    let html = fs.readFileSync(file, 'utf8');
    
    // Case-insensitive Passwortprüfung
    html = html.replace(/s\.value/g, 's.value.toLowerCase()');
    
    // Box im CSS vergrößern, damit das Kontaktformular hineinpasst
    html = html.replace(/height:170px/g, 'height:auto;min-height:170px');
    
    // Formular unter dem Passwort-Formular einfügen
    html = html.replace('</form></div>', `</form>${contactFormHtml}</div>`);
    
    fs.writeFileSync(file, html);
    console.log(`✅ ${file} ist jetzt mit Passwort "${password}", Kontaktformular und Datenschutzhinweis geschützt.`);
}

encryptFile('index.html', 'freiheit');
if (fs.existsSync('index_en.html')) {
    encryptFile('index_en.html', 'freiheit');
}

// Aufräumen der temporären Testdatei falls vorhanden
if (fs.existsSync('index_encrypted.html')) {
    fs.unlinkSync('index_encrypted.html');
}
