const editor = CodeMirror.fromTextArea(document.getElementById('codeEditor'), {
    lineNumbers: true,
    mode: 'python',
    theme: 'pycar-theme',
    lineWrapping: true, 
    tabSize: 4,
    indentUnit: 4,
    indentWithTabs: false,
    smartIndent: true,
    extraKeys: {},
    autoCloseBrackets: true,
    hintOptions: {
        completeSingle: false
    }
});

editor.on('inputRead', async function(cm, change) {
    
    if (change.text[0].match(/[a-zA-Z0-9_]/)) {
        CodeMirror.commands.autocomplete(cm);
    }
});

var pg = document.querySelector('.progress_bar .progress_bar_inner');
async function update_pg() {
    fetch('/get_symbols', {
        method: 'GET'
    })
    .then((r) => r.json())
    .then((data) => {

        if (data.error == 'Not enough symbols') {
            pg.style.height = `0%`;
            return;
        }
            
        pg.style.height = `${data.symbols_left / data.symbols_total * 100}%`;
        console.log(data);
        
        
    });
}
update_pg();
shakeTimeouts = [];

editor.on('change', (cm, change) => {

    console.log(change);
    if (change.origin == 'setValue') return;

    fetch('/update_code', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({text: cm.getValue()})
    })
    .then((r) => r.json())
    .then(async (data) => {
        await update_pg();

        if (data.error == 'Not enough symbols') {
            pg.parentElement.classList.add('shake');
            shakeTimeouts.forEach(e => {
                clearTimeout(e);
            });
            const timeout = setTimeout(() => {
                pg.parentElement.classList.remove('shake');
            }, 700);
            shakeTimeouts.push(timeout);
            cm.setValue(data.text);
            return;
        }
        
        const cursor = editor.getCursor();
        cm.setValue(data.text);
        editor.setCursor(cursor);
    });

});