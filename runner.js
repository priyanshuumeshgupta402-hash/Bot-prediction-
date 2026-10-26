const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');

async function getExactHTMLMessage() {
    return new Promise((resolve, reject) => {
        try {
            const htmlPath = path.join(__dirname, 'deepseek_html_20261026_a886de.html');
            const htmlContent = fs.readFileSync(htmlPath, 'utf8');

            const virtualConsole = new VirtualConsole();
            const dom = new JSDOM(htmlContent, {
                runScripts: "dangerously",
                resources: "usable",
                virtualConsole
            });

            const { window } = dom;

            let checks = 0;
            const interval = setInterval(() => {
                checks++;
                if (window.activePred && window.activePred.period) {
                    clearInterval(interval);
                    
                    const pred = window.activePred;
                    const periodShort = String(pred.period).slice(-3);
                    const boldPeriod = window.toBoldUnicode("PERIOD NO - " + periodShort);
                    const boldBetType = window.toBoldUnicode(pred.betType);
                    const boldNums = window.toBoldUnicode(pred.n1 + " , " + pred.n2);
                    
                    const exactText = `‼️ ${boldPeriod}\n\n📈 ${boldBetType} ➔ ${boldNums}`;
                    
                    resolve({
                        period: periodShort,
                        betType: pred.betType,
                        n1: pred.n1,
                        n2: pred.n2,
                        exactText: exactText
                    });
                }

                if (checks > 30) {
                    clearInterval(interval);
                    reject(new Error("HTML Engine Timeout"));
                }
            }, 500);

        } catch (err) {
            reject(err);
        }
    });
}

getExactHTMLMessage()
    .then(data => console.log(JSON.stringify(data)))
    .catch(err => {
        console.error(JSON.stringify({ error: err.message }));
        process.exit(1);
    });
