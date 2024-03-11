const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsHost = window.location.hostname;
const wsPort = window.location.port;
const ws = new WebSocket(`${wsProtocol}//${wsHost}:${wsPort}`);
ws.binaryType = 'arraybuffer';

ws.onopen = () => {
    console.log("Connected");
};

let dimsSet = false;

ws.onmessage = (evt) => {
  const bytes = new Uint8Array(evt.data);
  const blob = new Blob([bytes.buffer], { type: 'image/jpeg' });

  const imageURL = URL.createObjectURL(blob);
  document.getElementById('imagefeed').src = imageURL;

  if (!dimsSet) {
    dimsSet = true;
    const tempImage = new Image();
    tempImage.src = imageURL;
    tempImage.onload = function() {
      canvasWidth = tempImage.width;
      canvasHeight = tempImage.height;
      new p5(sketch);
      adjustCanvasScale();
    };
  }
};