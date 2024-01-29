import sys
import av
import cv2
import configparser
import collections
from datetime import datetime
import numpy as np
import base64

CONFIG_ERROR = 5

def grayscale(pxl):
    return 0.114*pxl[0] + 0.587*pxl[1] + 0.299*pxl[2]

def getOutFileName():
    return datetime.now().strftime(NAME + '-%Y-%m-%d_%H-%M-%S')

def setConfigurations():
    filepath = sys.argv[1] if len(sys.argv) > 1 else 'config.ini'
    config = configparser.ConfigParser()
    config.read(filepath)

    global CAMERA_PATH, NAME, PIXEL_THRESHOLD, ALARM_THRESHOLD, PIXEL_STEP, FRAMES_AFTER_ALARM, BUFFER_SIZE

    CAMERA_PATH = config['Camera']['camera_path']
    NAME = config['Camera']['name']
    PIXEL_THRESHOLD = int(config['MotionSettings']['pixel_threshold'])
    ALARM_THRESHOLD = int(config['MotionSettings']['alarm_threshold'])
    PIXEL_STEP = int(config['MotionSettings']['pixel_step'])
    FRAMES_AFTER_ALARM = int(config['VideoSettings']['frames_after_alarm'])
    BUFFER_SIZE = int(config['VideoSettings']['buffer_size'])

def main():
    try:
        setConfigurations()
    except Exception as e:
        print(e)
        exit(CONFIG_ERROR)
    video = av.open(CAMERA_PATH, 'r', options={'rtsp_transport':'tcp'})

    in_stream = video.streams.video[0]

    output = None
    out_stream = None
    base_timestamp = None  # Stores the first timestamp when alarm triggers

    alarm = False
    frames_since_thresh = 0
    img_last = None

    buffer = collections.deque()

    try:
        for packet in video.demux(in_stream):
            for frame in packet.decode():
                
                img = frame.to_ndarray(format='bgr24')
                f = open('IMG_0920.JPG', 'rb')
                encodedString = base64.b64encode(f.read())
                sys.stdout.buffer.write(encodedString)
                # image_bytes = np.clip(img, 0, 255).astype(np.uint8).tobytes()
                # sys.stdout.buffer.write(image_bytes)
                sys.stdout.flush()

                count = 0
                img_draw = img.copy()
                if img_last is not None:
                    for y in range(0, len(img), PIXEL_STEP):
                        for x in range(0, len(img[0]), PIXEL_STEP):
                            if abs(grayscale(img[y, x]) - grayscale(img_last[y, x])) > PIXEL_THRESHOLD:
                                for k in range(0, 3):
                                    for l in range(0, 3):
                                        img_draw[y+k, x+l] = [0, 0, 255]
                                count += 1
                img_last = img

                if count > ALARM_THRESHOLD:
                    frames_since_thresh = 0
                    if not alarm:
                        alarm = True
                        print("--- Writing to file")
                        output = av.open(getOutFileName()+'.mp4', 'w', format='mp4')
                        out_stream = output.add_stream(template=in_stream)

                        # TODO: Fix timestamp 
                        # First packet in buffer has pts=None and dts=None
                        base_timestamp = buffer[0].pts if buffer[0].pts else 0
                        # print(buffer)

                        for p in buffer:
                            if p.pts and p.dts:
                                p.pts -= base_timestamp
                                p.dts -= base_timestamp
                            p.stream = out_stream
                            output.mux(p)
                        buffer.clear()
                    
                else:
                    frames_since_thresh += 1
                    if alarm:
                        if frames_since_thresh > FRAMES_AFTER_ALARM and alarm:
                            alarm = False
                            print("--- Closing file")
                            output.close()
                            base_timestamp = None 

                cv2.imshow("Video", img_draw)
                print(count, "Alarm:", alarm)

            if alarm:
                if base_timestamp is not None:
                    packet.pts -= base_timestamp
                    packet.dts -= base_timestamp
                packet.stream = out_stream
                output.mux(packet)

            else:
                if len(buffer) == BUFFER_SIZE:
                    buffer.popleft()

                if packet.pts is not None:
                    buffer.append(packet)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
    except KeyboardInterrupt:
        pass

    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()