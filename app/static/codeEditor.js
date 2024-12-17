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

editor.on('change', (cm, change) => {
    fetch('/update_code', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({text: cm.getValue()})
    })
    .then((r) => r.json())
    .then((data) => {
        console.log(data);
        
    });
});