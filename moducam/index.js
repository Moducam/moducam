const fs = require('fs');
const ini = require('ini');
const { spawn } = require('child_process');
const CONFIG_PATH = '../config.ini';

let config = ini.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'))
var pythonProcess = spawn('/usr/bin/python', ['../cam.py', CONFIG_PATH]);
setProcessEvents();

exports.restart = function() {
    if (pythonProcess) {
        pythonProcess.kill('SIGINT');
    } else {
        pythonProcess = spawn('/usr/bin/python', ['../cam.py', CONFIG_PATH]);
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
        pythonProcess = spawn('/usr/bin/python', ['../cam.py', CONFIG_PATH]);
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