const fs = require('fs');
const ini = require('ini');
const { spawn } = require('child_process');
const CONFIG_PATH = '../config.ini';
const WebSocket = require("ws");

const io = require('socket.io')

let config = ini.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'))
var pythonProcess = spawn('/opt/homebrew/opt/python@3.11/bin/python3.11', ['../cam.py', CONFIG_PATH]);
setProcessEvents();

const wss = new WebSocket.Server({
    port: 8080
});

wss.on("connection", function connection(ws) {
    console.log("Client conneted to websocket");
});

// listen for the new image
pythonProcess.stdout.on("data", (data) => {
    // broadcast the new binary image to all clients
    wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(data, { binary: true });
        }
    });
    io.emit('image', data)
});

exports.restart = function() {
    if (pythonProcess) {
        pythonProcess.kill('SIGINT');
    } else {
        pythonProcess = spawn('/opt/homebrew/opt/python@3.11/bin/python3.11', ['../cam.py', CONFIG_PATH]);
        setProcessEvents();
    }
}

function setProcessEvents() {
    pythonProcess.on('close', (code, signal) => {
        console.log("CLOSE EVENT " + code);
        if (code == 5) {
            console.log("There are problems with your config file. Please fix and restart!");
            pythonProcess = null;
            return;
        }
        pythonProcess = spawn('/opt/homebrew/opt/python@3.11/bin/python3.11', ['../cam.py', CONFIG_PATH]);
        setProcessEvents();
    });
}

exports.updateConfigFile = function(new_configs) {
    // console.log(new_configs)

    for (const key in config) {
        for (const property in config[key]) {
            if (new_configs.hasOwnProperty(property)) {
                config[key][property] = new_configs[property]
            }
        }
    }

    fs.writeFileSync('../config_modified.ini', ini.stringify(config));
}