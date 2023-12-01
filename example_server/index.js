const moducam = require('moducam');
const express = require('express');

const app = express();
const port = 3000;

app.use(express.urlencoded({
    extended: true
}))

// get UI
app.get('/cam', (req, res) => {
    res.sendFile(__dirname + '/public/ui.html');
});

// update config file
app.post('/cam', (req, res) => {
    moducam.updateConfigFile(req.body);
    res.sendStatus(200)
});

// kill python process and restart
app.post('/restart', (req, res) => {
    moducam.restart();
    res.sendStatus(200)

});

app.get('/', (req, res) => {
    res.send('Hello World!');
});

app.listen(port, () => {
    console.log(`Listening at http://localhost:${port}`);
});