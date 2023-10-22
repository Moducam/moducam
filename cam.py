import av
import cv2
from datetime import datetime

def grayscale(pxl):
    return 0.114*pxl[0] + 0.587*pxl[1] + 0.299*pxl[2]

def getOutFileName():
    return datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

dicOption={'rtsp_transport':'tcp'}
video = av.open('***REMOVED***', 'r', options=dicOption)

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
                        if abs(grayscale(img[y, x]) - grayscale(img_last[y, x])) > 20:
                            for k in range(0, 3):
                                for l in range(0, 3):
                                    img_draw[y+k, x+l] = [0, 0, 255]
                            count += 1
            img_last = img

            if count > 30 and not alarm:
                alarm = True
                print("Writing to file")
                output = av.open(getOutFileName()+'.mp4', 'w', format='mp4')
                out_stream = output.add_stream(template=in_stream)
                base_timestamp = packet.pts
                frames_since_thresh = 0
            else:
                frames_since_thresh += 1
                if alarm:
                    if frames_since_thresh > 80 and alarm:
                        alarm = False
                        print("Closing file")
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
