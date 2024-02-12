const fs = require('fs');
const ini = require('ini');
const { spawn, exec } = require('child_process');
const CONFIG_PATH = '../config.ini';
const WebSocket = require("ws");

let config = ini.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'));
let pythonPath;
let pythonProcess;

exec('which python3', (error, stdout, stderr) => {
    pythonPath = stdout.trim()
    pythonProcess = spawn(pythonPath, ['../cam.py', CONFIG_PATH, '--pipe']);
    setProcessEvents();
})

const wss = new WebSocket.Server({
    port: 8080
});

wss.on("connection", function connection(ws) {
    console.log("Client conneted to websocket");
});

const path = 'my_pipe';
let fifo = spawn('mkfifo', [path])

fifo.on('exit', function(status) {
    console.log('Created Pipe');

    const fd  = fs.openSync(path, 'r+');
    let fifoRs = fs.createReadStream(null, { fd });

    image = ''
    image = Buffer.alloc(0);

    fifoRs.on('data', data => {
        image = Buffer.concat([image, data]);

        if (data.length < 8192) {
            wss.clients.forEach((client) => {
                if (client.readyState === WebSocket.OPEN) {
                    client.send(image, {binary : true});
                }
            });
            image = Buffer.alloc(0);
        }
    });
});

exports.restart = function() {
    if (pythonProcess) {
        pythonProcess.kill('SIGINT');
    } else {
        pythonProcess = spawn(pythonPath, ['../cam.py', CONFIG_PATH, '--pipe']);
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
        pythonProcess = spawn(pythonPath, ['../cam.py', CONFIG_PATH, '--pipe']);
        setProcessEvents();
    });
}

exports.updateConfigFile = function(new_configs) {
    for (const key in config) {
        for (const property in config[key]) {
            if (new_configs.hasOwnProperty(property)) {
                config[key][property] = new_configs[property]
            }
        }
    }

    fs.writeFileSync('../config_modified.ini', ini.stringify(config));
}