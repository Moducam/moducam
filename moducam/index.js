const fs = require('fs');
const ini = require('ini');
const { spawn, exec } = require('child_process');
const WebSocket = require("ws");

let config;
let pythonPath;
let pythonProcess;
let configPath
let arglist;

exports.startModucam = function(moducamPath, confPath, videoDir) {
    arglist = [moducamPath];
    arglist.push("-c", confPath);
    arglist.push("--pipe");
    arglist.push(videoDir);

    config = ini.parse(fs.readFileSync(confPath, 'utf-8'));
    configPath = confPath

    exec('which python3', (error, stdout, stderr) => {
        pythonPath = stdout.trim()
        pythonProcess = spawn(pythonPath, arglist);
        setProcessEvents();
    })
}

exports.startWebSocketServer = function(httpServer) {
    const wss = new WebSocket.Server({
        server: httpServer
    });

    wss.on("connection", function connection(ws) {
        console.log("Client conneted to websocket");
    });

    const path = 'my_pipe';
    let fifo = spawn('mkfifo', [path]);

    fifo.on('exit', function(status) {
        console.log('Created Pipe');

        const fd  = fs.openSync(path, 'r+');
        let fifoRs = fs.createReadStream(null, { fd });

        image = ''
        image = Buffer.alloc(0);

        fifoRs.on('data', data => {
            image = Buffer.concat([image, data]);
            //process.stdout.write("new data ");
            if (data.length % 8192 != 0) {
                //console.log("-----END ");
                wss.clients.forEach((client) => {
                    if (client.readyState === WebSocket.OPEN) {
                        client.send(image, {binary : true});
                    }
                });
                image = Buffer.alloc(0);
            }
        });
    });

}

exports.restart = function() {
    if (pythonProcess) {
        pythonProcess.kill('SIGINT');
    } else {
        pythonProcess = spawn(pythonPath, arglist);
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
        pythonProcess = spawn(pythonPath, arglist);
        setProcessEvents();
    });
}

exports.updateConfigFile = function(new_configs) {
    for (const key in config) {
        for (const property in config[key]) {
            if (new_configs[key].hasOwnProperty(property)) {
                if (property === "zone_points") {
                    new_configs[key][property] = convertPointsFromJson(new_configs[key][property]);
                }
                config[key][property] = new_configs[key][property]
            }
        }
    }

    fs.writeFileSync(configPath, ini.stringify(config));
    
    //TEMPORARY FOR DEMO
    exports.restart();
}

exports.getConfig = function() {
    const converted = JSON.parse(JSON.stringify(config));
    converted["Zone"]["zone_points"] = convertPointsToJson(config["Zone"]["zone_points"])
    return converted
}

function convertPointsFromJson(json) {
    return json.map(point => `(${point.x}, ${point.y})`).join(", ");
}

function convertPointsToJson(str) {
    const points = str.split("), ").map(point => 
        point.replace(/\(|\)/g, "")
        .split(", ")
        .map(Number)
    );
    
    const zonePoints = points.map(([x, y]) => ({ x, y }));
      
    return zonePoints;
}