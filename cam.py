import av
import cv2

dicOption={'rtsp_transport':'tcp'}
video = av.open('***REMOVED***', 'r', options=dicOption)
output = av.open('cam.mp4', 'w', format='mp4')

in_stream = video.streams.video[0]
out_stream = output.add_stream(template=in_stream)

try:
    for packet in video.demux(in_stream):
        print(packet)

        for frame in packet.decode():
            print(frame)
            img = frame.to_ndarray(format='bgr24')
            cv2.imshow("Video", img)

        packet.stream = out_stream

        output.mux(packet)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
except KeyboardInterrupt:
    pass

output.close()
cv2.destroyAllWindows()