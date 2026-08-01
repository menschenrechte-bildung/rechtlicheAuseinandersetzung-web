const { execSync } = require('child_process');
const fs = require('fs');

function encryptFile(file, password) {
    console.log(`Verschlüssele ${file}...`);
    // npx pagecrypt aufrufen
    execSync(`npx pagecrypt ${file} ${file} "${password}"`, { stdio: 'inherit' });
    
    // Nachbearbeiten: Groß-/Kleinschreibung beim Passwort ignorieren
    let html = fs.readFileSync(file, 'utf8');
    html = html.replace(/s\.value/g, 's.value.toLowerCase()');
    fs.writeFileSync(file, html);
    console.log(`✅ ${file} ist jetzt mit Passwort "${password}" (case-insensitive) geschützt.`);
}

encryptFile('index.html', 'freiheit');
if (fs.existsSync('index_en.html')) {
    encryptFile('index_en.html', 'freiheit');
}

// Aufräumen der temporären Testdatei falls vorhanden
if (fs.existsSync('index_encrypted.html')) {
    fs.unlinkSync('index_encrypted.html');
}
