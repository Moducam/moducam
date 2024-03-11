# Moducam
An easy-to-install modular camera surveillance system, with motion detection and an optional web interface written in Node.js

## Installation steps
1. Ensure you have Python3 and Node.js installed
2. Install Moducam dependencies: `pip3 install -r requirements.txt`
3. Modify your config.ini to set your camera path
4. Run with `python3 moducam.py`

### Node webserver
1. Ensure Moducam is not currently running
2. `cd example_server`
3. Install server dependencies: `npm i`
4. If you moved example_server out of the Moducam directory, you must specify where Moducam is located by setting `moducamPath` and `configPath` in index.js
5. Run with `node index.js`
6. By default, the server will be at http://localhost:3000

### Installation notes
If you cannot install Python modules globally on your system, you can run Moducam in a virtual environment. Just run either the script or the Node server with the virtual environment activated.
