const fs = require('fs');
const ini = require('ini');

let config = ini.parse(fs.readFileSync('../config.ini', 'utf-8'))

exports.restart = function() {
    
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