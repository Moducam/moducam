const fs = require('fs');
const ini = require('ini');
const { spawn } = require('child_process');

let config = ini.parse(fs.readFileSync('../config.ini', 'utf-8'))

exports.restart = function() {
    console.log('here')
    const pythonProcess = spawn('python3', ['../cam.py']);

    pythonProcess.stdout.on('data', (data) => {
        console.log(data)
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