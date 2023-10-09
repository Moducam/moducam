import av
import cv2

dicOption={'rtsp_transport':'tcp'}
video = av.open('***REMOVED***', 'r', options=dicOption)

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