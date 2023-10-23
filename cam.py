import av
import cv2
import configparser
from datetime import datetime

def grayscale(pxl):
    return 0.114*pxl[0] + 0.587*pxl[1] + 0.299*pxl[2]

def getOutFileName():
    return datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

def setConfigurations():
    config = configparser.ConfigParser()
    config.read('config.ini')

    global PIXEL_THRESHOLD, ALARM_THRESHOLD, FRAMES_AFTER_ALARM, BUFFER_SIZE

    PIXEL_THRESHOLD = int(config['VideoSettings']['pixel_threshold'])
    ALARM_THRESHOLD = int(config['VideoSettings']['alarm_threshold'])
    FRAMES_AFTER_ALARM = int(config['VideoSettings']['frames_after_alarm'])
    BUFFER_SIZE = int(config['VideoSettings']['buffer_size'])

def main():
    setConfigurations()
    video = av.open('rtsp://admin:penelope0903c@127.0.0.1:5540/cam/realmonitor?channel=1&subtype=0', 'r', options={'rtsp_transport':'tcp'})

    in_stream = video.streams.video[0]

    output = None
    out_stream = None
    base_timestamp = None  # Stores the first timestamp when alarm triggers

    alarm = False
    frames_since_thresh = 0
    img_last = None

    try:
        for packet in video.demux(in_stream):
            for frame in packet.decode():
                img = frame.to_ndarray(format='bgr24')

                count = 0
                img_draw = img.copy()
                if img_last is not None:
                    for y in range(0, len(img), 20):
                        for x in range(0, len(img[0]), 20):
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
                        base_timestamp = packet.pts
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

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
    except KeyboardInterrupt:
        pass

    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()