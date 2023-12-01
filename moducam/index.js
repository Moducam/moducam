const fs = require('fs');
const ini = require('ini');
const { spawn } = require('child_process');

let config = ini.parse(fs.readFileSync('../config.ini', 'utf-8'))

exports.restart = function() {
    console.log('here')
    const pythonProcess = spawn('/opt/homebrew/opt/python@3.11/bin/python3.11', ['../cam.py']);

    pythonProcess.stdout.on('data', (data) => {
        console.log(data)
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python stderr: ${data}`);
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