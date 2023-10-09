import av
import cv2

dicOption={'rtsp_transport':'tcp'}
video = av.open('rtsp://admin:penelope0903c@127.0.0.1:5540/cam/realmonitor?channel=1&subtype=0', 'r', options=dicOption)

try:
    for packet in video.demux():
        print(packet)
        for frame in packet.decode():
            if packet.stream.type == 'video':
                print(frame)
                img = frame.to_ndarray(format='bgr24')
                cv2.imshow("Video", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
except KeyboardInterrupt:
    pass
cv2.destroyAllWindows()