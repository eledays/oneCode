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
const socket = io();
var pg = document.querySelector('.progress_bar .progress_bar_inner');
var nextUpdateTimeout = null;


socket.on('connect', () => {
    console.log('Socket connected successfully');
});


socket.on('update_client', (data) => {
    // Обновление пользовательской страницы - код, прогресс бар
    console.log('updated', data);

    if (data.code) {
        var cursor = editor.getCursor();
        editor.setValue(data.code);
        editor.setCursor(cursor);
    }
    if (data.symbols) {
        pg.style.height = `${data.symbols.left / data.symbols.total * 100}%`;
        clearTimeout(nextUpdateTimeout);
        nextUpdateTimeout = setTimeout(() => {
            pg.style.height = '100%';
        }, Math.max(data.symbols.update_in * 1000, 0));
    }
});


editor.on('inputRead', async function(cm, change) {
    // Отображение подсказок при вводе
    if (change.text[0].match(/[a-zA-Z0-9_]/)) {
        CodeMirror.commands.autocomplete(cm);
    }
});


var shakeTimeouts = [];
editor.on('change', (cm, change) => {
    // Обработка изменения кода пользователем

    if (change.origin == 'setValue') return;
    
    socket.emit('update_server_code', cm.getValue(), (data) => {

        if (data.error == 'Not enough symbols') {
            // Недостаточно символов

            pg.parentElement.classList.add('shake');
            shakeTimeouts.forEach(e => {
                clearTimeout(e);
            });
            const timeout = setTimeout(() => {
                pg.parentElement.classList.remove('shake');
            }, 700);
            shakeTimeouts.push(timeout);
            // if (data.text) cm.setValue(data.text);
            return;
        }

        var cursor = editor.getCursor();
        if (data.text) cm.setValue(data.text);
        editor.setCursor(cursor);

    });
});