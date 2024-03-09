const fs = require('fs');
const http = require('http');
const express = require('express');
const moducam = require('moducam');

const app = express();
const server = http.createServer(app);
const port = process.env.PORT || 3000;
const videoDirectory = 'public/videos';

moducam.startModucam('../cam.py', '../config.ini', videoDirectory);
moducam.startWebSocketServer(server);

app.use(express.urlencoded({
    extended: true
}))
app.use(express.json());

// get UI
app.get('/', (req, res) => {
    res.sendFile(__dirname + '/ui.html');
});

// get zone UI
app.get('/zone', (req, res) => {
    res.sendFile(__dirname + '/zone.html');
});

// get playback UI
app.get('/playback', (req, res) => {
    res.sendFile(__dirname + '/playback.html')
});

app.get('/videolist', (req, res) => {
    fs.readdir(videoDir, (err, files) => {
        let list = []
        files.forEach(file => {
            list.push(file.split('.')[0])
        });
        res.send(list)
    });
});

// update config file
app.post('/config', (req, res) => {
    moducam.updateConfigFile(req.body);
    res.sendStatus(200)
});

// kill python process and restart
app.post('/restart', (req, res) => {
    moducam.restart();
    res.sendStatus(200)

});

// use public folder for anything else
app.use('/', express.static(__dirname + '/public'));

app.get('/config', (req, res) => {
    val = moducam.getConfig();
    if (val)
        res.send(val);
    else
        res.sendStatus(404);
})

app.get('/', (req, res) => {
    res.send('Hello World!');
});

server.listen(port, () => {
    console.log(`Listening at http://localhost:${port}`);
});