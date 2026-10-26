const path = require('path');
const puppeteer = require('puppeteer');

async function getLivePrediction() {
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const page = await browser.newPage();
    
    // Aapki original HTML file ko load karega
    const htmlPath = 'file://' + path.resolve(__dirname, 'deepseek_html_20261026_a886de.html');
    await page.goto(htmlPath, { waitUntil: 'networkidle0' });

    // HTML file ke andar data load hone ka wait karega
    await page.waitForFunction(() => {
        const p = document.getElementById('nextP')?.innerText;
        const r = document.getElementById('res')?.innerText;
        return p && p !== '----' && r && r !== 'WAIT';
    }, { timeout: 20000 });

    // HTML file ke DOM se exact live values extract karega
    const data = await page.evaluate(() => {
        const periodFull = document.getElementById('nextP').innerText.trim();
        const betType = document.getElementById('res').innerText.trim();
        const numsText = document.getElementById('numVal').innerText.trim();
        
        const periodShort = periodFull.slice(-3);
        const parts = numsText.split(',').map(s => s.trim());
        const n1 = parts[0] || '5';
        const n2 = parts[1] || '8';

        function toBold(str) {
            const map = {
                '0':'𝟬','1':'𝟭','2':'𝟮','3':'𝟯','4':'𝟰','5':'𝟱','6':'𝟲','7':'𝟳','8':'𝟴','9':'𝟵',
                'A':'𝗔','B':'𝗕','C':'𝗖','D':'𝗗','E':'𝗘','F':'𝗙','G':'𝗚','H':'𝗛','I':'𝗜','J':'𝗝',
                'K':'𝗞','L':'𝗟','M':'𝗠','N':'𝗡','O':'𝗢','P':'𝗣','Q':'𝗤','R':'𝗥','S':'𝗦','T':'𝗧',
                'U':'𝗨','V':'𝗩','W':'𝗪','X':'𝗫','Y':'𝗬','Z':'𝗭','a':'𝗮','b':'𝗯','c':'𝗰','d':'𝗱',
                'e':'𝗲','f':'𝗳','g':'𝗴','h':'𝗵','i':'𝗶','j':'𝗷','k':'𝗸','l':'𝗹','m':'𝗺','n':'𝗻',
                'o':'𝗼','p':'𝗽','q':'𝗾','r':'𝗿','s':'𝘀','t':'𝘁','u':'𝘂','v':'𝘃','w':'𝘄','x':'𝘅',
                'y':'𝘆','z':'𝘇','(': '(',' )': ')',',': ',', ' ': ' ','-': '-'
            };
            return String(str).split('').map(c => map[c] || c).join('');
        }

        const boldPeriod = toBold("PERIOD NO - " + periodShort);
        const boldBetType = toBold(betType);
        const boldNums = toBold(n1 + " , " + n2);
        const exactText = `‼️ ${boldPeriod}\n\n📈 ${boldBetType} ➔ ${boldNums}`;

        return {
            period: periodShort,
            betType: betType,
            n1: n1,
            n2: n2,
            exactText: exactText
        };
    });

    await browser.close();
    return data;
}

getLivePrediction()
    .then(res => console.log(JSON.stringify(res)))
    .catch(err => {
        console.error(JSON.stringify({ error: err.message }));
        process.exit(1);
    });
