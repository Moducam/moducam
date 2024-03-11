# Moducam
An easy-to-install modulcar security camera system, with an optional web interface written in Node.js

## Installation steps
1. Ensure you have python3 and node installed
2. Install moducam dependencies: `pip3 install -r requirements.txt`
3. Modify your config.ini to set your camera path
4. Run with `python3 moducam.py`

### Node webserver
1. Ensure moducam is not currently running
2. `cd example_server`
3. Install server dependencies: `npm i`
4. If you moved example_server out of the moducam directory, you must specify where moducam is located by setting `moducamPath` and `configPath` in index.js
5. Run with `node index.js`
6. By default, the server will be at http://localhost:3000
