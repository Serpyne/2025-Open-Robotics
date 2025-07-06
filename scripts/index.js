const editor = ace.edit("editor");
editor.setTheme("ace/theme/monokai");
editor.session.setMode("ace/mode/python");
editor.setOption("copyWithEmptySelection", true);
editor.setOptions({
    fontSize: "14px",
    enableBasicAutocompletion: true,
    enableLiveAutocompletion: true,
    showPrintMargin: false
});

const themeToggle = document.getElementById('themeToggle');
themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('light-mode');
    const isLight = document.body.classList.contains('light-mode');
    
    themeToggle.textContent = isLight ? '☀️' : '🌙';
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
    
    const editor = ace.edit("editor");
    editor.setTheme(isLight ? "ace/theme/chrome" : "ace/theme/monokai");
    
    const consoleContainer = document.querySelector('.console-container');
    consoleContainer.classList.toggle('light-console', isLight);
});

if (localStorage.getItem('theme') === 'light') {
    document.body.classList.add('light-mode');
    themeToggle.textContent = '☀️';
    ace.edit("editor").setTheme("ace/theme/chrome");
    document.querySelector('.console-container').classList.add('light-console');
}

const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.querySelector('.sidebar');
const mobileExecuteButton = document.getElementById('mobileExecuteButton');
sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
    sidebarToggle.textContent = sidebar.classList.contains('collapsed') ? '≡' : '☰';
    mobileExecuteButton.style.display = sidebar.classList.contains('collapsed') ? 'block' : 'none';
});

const consoleOutput = document.getElementById('consoleOutput');
const autoscrollCheckbox = document.getElementById('autoscrollCheckbox');

function appendToConsole(text) {
    consoleOutput.textContent += text;
    if (autoscrollCheckbox.checked) {
        consoleOutput.scrollTop = consoleOutput.scrollHeight;
    }
    
    let cmd = text.split(" ")[0];
    if (cmd == "DrawPoints") {
        text = text.substring(11, text.length);
        let s = text.substring(1, text.length - 1);
        let points = s.split("] [");
        for (let i in points) {
            points[i] = points[i].split(", ");
            points[i] = [parseInt(points[i][0]), parseInt(points[i][1])]
        }
        tofPoints = points;
    }
    else if (cmd == "DrawRect") {
        s = text.substring(9, text.length);
        let c = s.split(" ");
        x = parseInt(c[0]);
        y = parseInt(c[1]);
        w = parseInt(c[2]);
        h = parseInt(c[3]);
        drawRect(x,y,w,h);
    }
}

const fileList = document.getElementById('fileList');

const select = document.getElementById('fileList');
select.addEventListener("change", () => {
    setTimeout("loadFile();", 200);
});
            
function updateFileList() {
    fetch('/list')
        .then(response => response.text())
        .then(data => {
            const files = data.split('\n');
            select.innerHTML = '';
            files.forEach(file => {
                const option = document.createElement('option');
                option.text = file;
                select.add(option);
            });
        });
}

function newFile() {
    fetch(`/new`)
        .then(response => response.text())
        .then(data => {
            let filename = data.toString();
            console.log(filename);
            updateFileList();
            setTimeout(`document.getElementById('fileList').value = '${filename}';`, 100);
            setTimeout("loadFile();", 200);
            showToast(`New file '${filename}' created.`);
        });
}

function confirmArchive() {
    const selectedFile = fileList.value;
    
    if (!selectedFile) {
        appendToConsole('> No file selected');
        return;
    }

    if (confirm(`Are you sure you want to archive "${selectedFile}"? This action cannot be undone.`)) {
        archiveFile();
    } else {
        appendToConsole('> Delete canceled');
    }
}
function archiveFile() {
    const filename = fileList.value;
    fetch(`/archive/${filename}`)
        .then(response => response.text())
        .then(data => {
            updateFileList();
            setTimeout("loadFile();", 100);
            showToast(`'${filename}' deleted.`);
        });
}

function loadFile() {
    const filename = fileList.value;
    fetch(`/load/${filename}`)
        .then(response => response.text())
        .then(data => {
            editor.setValue(data);
        });
}

function saveFile() {
    const filename = fileList.value;
    const content = editor.getValue();
    fetch('/save', {
        method: 'POST',
        body: `${filename}:${content}`
    }).then(response => {
        showToast(`'${filename}' saved.`);
    });
}

const autoScrollButton = document.getElementById("autoscrollCheckbox");
var autoScroll = true;
autoScrollButton.checked = autoScroll;
autoScrollButton.onchange = function(event) {
    autoScroll = autoScrollButton.checked;
}

const executeButton = document.getElementById("executeButton");
const outputBox = document.getElementById("output");

function renameFile() {
    const filename = fileList.value;
    const newName = document.getElementById('renameInput').value;
    fetch(`/rename`, {
        method: 'POST',
        body: `${filename}:${newName}`
    }).then(response => response.text())
        .then(data => {
        updateFileList();
        if (data) {
            setTimeout(`fileList.value = '${data}';`, 200);
            showToast(`File '${filename}' renamed to '${data}'.`);
        }
    })
}

var socket;
var codeRunning = false;
function executeFile() {
    executeButton.innerText = "Stop";
    mobileExecuteButton.innerText = "Stop";
    
    const filename = fileList.value;
    
    fetch(`/execute`, {
        method: 'POST',
        body: filename
    }).then(response => response.text())
        .then(data => {
    console.log(data);
    if (data == "SCRIPT_START_SIGNAL") {
        codeRunning = true;
        console.log(window.href);
        socket = new WebSocket(`ws://raspberrypi.local:8765/${filename}`);
        socket.onmessage = function(event) {
        if (event.data == "SCRIPT_ENDED_SIGNAL") {
            executeButton.innerText = "Run";
            mobileExecuteButton.innerText = "Run";
            showToast(`'${filename}' ended.`)
            return;
        }
        appendToConsole(event.data);
    };
    } else if (data == "SCRIPT_END_SIGNAL") {
        socket.close();
        codeRunning = false;
    }
    });
}

function clearOutput() {
    outputBox.innerText = "";
}

document.addEventListener('keydown', e => {
    if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        saveFile();
    }
});

let icon = {
    success:
    '<span class="material-symbols-outlined">task_alt</span>',
    danger:
    '<span class="material-symbols-outlined">error</span>',
    warning:
    '<span class="material-symbols-outlined">warning</span>',
    info:
    '<span class="material-symbols-outlined">info</span>',
};
function showToast(
    message = "Sample Message",
    toastType = "info",
    duration = 5000) {
    if (!Object.keys(icon).includes(toastType))
        toastType = "info";

    let box = document.createElement("div");
    box.classList.add(
        "toast", `toast-${toastType}`);
    box.innerHTML = ` <div class="toast-content-wrapper">
                <div class="toast-icon">
                ${icon[toastType]}
                </div>
                <div class="toast-message">${message}</div>
                <div class="toast-progress"></div>
                </div>`;
    duration = duration || 5000;
    box.querySelector(".toast-progress").style.animationDuration =
            `${duration / 1000}s`;

    let toastAlready = 
        document.body.querySelector(".toast");
    if (toastAlready) {
        toastAlready.remove();
    }

    document.body.appendChild(box)
};

function getLastOpenedFile() {
    fetch(`/load/`)
        .then(response => response.text())
        .then(data => {
            if (!data)
                return;
            fileList.value = data;
            setTimeout("loadFile();", 150);
        });
}

updateFileList();
setTimeout("getLastOpenedFile();", 200);
