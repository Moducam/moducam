const express = require('express');
const moducam = require('moducam');

const app = express();
const port = 3000;

app.use(express.urlencoded({
    extended: true
}))
app.use(express.json());

// get UI
app.get('/cam', (req, res) => {
    res.sendFile(__dirname + '/public/ui.html');
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

// get zone UI
app.get('/cam/zone', (req, res) => {
    res.sendFile(__dirname + '/public/zone.html');
});

// get library files
app.use('/lib', express.static(__dirname + '/public/lib'));

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

app.listen(port, () => {
    console.log(`Listening at http://localhost:${port}`);
});