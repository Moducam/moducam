const fs = require('fs');
const ini = require('ini');
const { spawn } = require('child_process');
const CONFIG_PATH = '../config.ini';
const WebSocket = require("ws");

let config = ini.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'))
var pythonProcess = spawn('/opt/homebrew/opt/python@3.11/bin/python3.11', ['../cam.py', CONFIG_PATH, true]);
setProcessEvents();

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

    console.log('Ready to write')

    image = ''
    image = Buffer.alloc(0);

    fifoRs.on('data', data => {
        image = Buffer.concat([image, data]);

        // 2196 should be last packet
        // if (image.length == 2418836) {
        if (data.length < 8192) {
            console.log('sending');
            wss.clients.forEach((client) => {
                if (client.readyState === WebSocket.OPEN) {
                    client.send(image, {binary : true});
                }
            });
            image = Buffer.alloc(0);
        }
    });
});

// listen for the new image
// pythonProcess.stdout.on("data", (data) => {
//     console.log(data)
//     let buf = Buffer.from(data);
//     console.log(buf)
//     fs.writeFileSync("new-path.jpg", data);

//     // broadcast the new binary image to all clients
//     wss.clients.forEach((client) => {
//         if (client.readyState === WebSocket.OPEN) {
//             client.send(base64);
//         }
//     });
// });

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