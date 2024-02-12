import sys
import av
import cv2
import configparser
import collections
from datetime import datetime
import numpy as np
import os

CONFIG_ERROR = 5

def grayscale(pxl):
    return 0.114*pxl[0] + 0.587*pxl[1] + 0.299*pxl[2]

def getOutFileName():
    return datetime.now().strftime(NAME + '-%Y-%m-%d_%H-%M-%S')

def setConfigurations():
    filepath = sys.argv[1] if len(sys.argv) > 1 else 'config.ini'

    config = configparser.ConfigParser()
    config.read(filepath)

    global CAMERA_PATH, NAME, PIXEL_THRESHOLD, ALARM_THRESHOLD, PIXEL_STEP, ZONE_POINTS, FRAMES_AFTER_ALARM, BUFFER_SIZE, PIPE

    if sys.argv[-1] == '--pipe':
        PIPE = True
    else:
        PIPE = False

    CAMERA_PATH = config['Camera']['camera_path']
    if CAMERA_PATH[0] == CAMERA_PATH[-1] == "\"":
        CAMERA_PATH = CAMERA_PATH[1:-1]

    NAME = config['Camera']['name']
    PIXEL_THRESHOLD = int(config['MotionSettings']['pixel_threshold'])
    ALARM_THRESHOLD = int(config['MotionSettings']['alarm_threshold'])
    PIXEL_STEP = int(config['MotionSettings']['pixel_step'])
    ZONE_POINTS = list(eval(config['Zone']['zone_points']))
    FRAMES_AFTER_ALARM = int(config['VideoSettings']['frames_after_alarm'])
    BUFFER_SIZE = int(config['VideoSettings']['buffer_size'])

def compute_zone(points, width, height):
    if len(points) > 0:
        if points[0] != points[-1]:
            points.append(points[0])
        if len(points) < 4:
            print("ERROR: Zone cannot be defined by less than 3 points")
            exit(CONFIG_ERROR)

    ranges = []
    for y in range(height):
        intercepts = []
        for i in range(len(points)-1):
            p1_x, p1_y = points[i]
            p2_x, p2_y = points[i+1]
            # Check if line intersects this row
            if min(p1_y, p2_y) <= y <= max(p1_y, p2_y):
                # Find the intercept
                if p2_x - p1_x == 0 or p2_y - p1_y == 0: # Vertical or horizontal
                    intercept = p2_x
                else:
                    slope = (p2_y - p1_y) / (p2_x - p1_x)
                    intercept = p1_x + (y - p1_y) / slope

                # Do we keep this intercept?
                if y == p1_y and intercept == p1_x:  # Check if intercept is a vertex
                    prev_x, prev_y = points[:-1][i-1]
                    if y >= min(prev_y, p2_y) and y <= max(prev_y, p2_y):
                        # y is not atop a hill or in a ditch -- discard duplicate
                        continue
                intercepts.append(round(intercept))

        if len(intercepts) % 2 != 0:  # Should never happen
            print("ERROR: Row has odd number of intercepts:")
            print(intercepts)
            exit(-1)
        
        intercepts.sort()

        # Couple up x-intercepts for this row to make tuple ranges
        row_ranges = []
        for i in range(0, len(intercepts), 2):
            row_ranges.append( (intercepts[i], intercepts[i+1]) )

        ranges.append(row_ranges)
    return ranges

def main():
    try:
        setConfigurations()
    except Exception as e:
        print(e)
        exit(CONFIG_ERROR)        

    points = ZONE_POINTS

    video = av.open(CAMERA_PATH, 'r', options={'rtsp_transport':'tcp'})
    in_stream = video.streams.video[0]

    output = None
    out_stream = None
    base_timestamp = None  # Stores the first timestamp when alarm triggers

    alarm = False
    frames_since_thresh = 0
    img_last = None

    buffer = collections.deque()

    scan_ranges = compute_zone(points, in_stream.width, in_stream.height)

    if PIPE:
        pipe_path = 'my_pipe'
        pipe_fd = os.open(pipe_path, os.O_WRONLY)

    try:
        for packet in video.demux(in_stream):
            for frame in packet.decode():
                img = frame.to_ndarray(format='bgr24')

                is_success, im_buf_arr = cv2.imencode(".jpeg", img)
                image_data = im_buf_arr.tobytes()

                if PIPE:
                    with open(pipe_path, 'wb') as pipe:
                        pipe.write(image_data)
                        pipe.flush()

                count = 0
                outcount = 0 # FOR TESTING
                img_draw = img.copy()
                if img_last is not None:
                    for y in range(0, len(scan_ranges), PIXEL_STEP):
                        for r in scan_ranges[y]:
                            for x in range(r[0], r[1], PIXEL_STEP):
                                # First step: Pixel color check
                                if abs(grayscale(img[y, x]) - grayscale(img_last[y, x])) > PIXEL_THRESHOLD:
                                    count += 1
                                    # Second step: Filter pixel by checking surrounding area
                                    filtercount = 0
                                    for k in range(0, 3):
                                        if abs(grayscale(img[y-1, x-1+k]) - grayscale(img_last[y-1, x-1+k])) > PIXEL_THRESHOLD:
                                            filtercount += 1
                                    for k in range(0, 3):
                                        if abs(grayscale(img[y+1, x-1+k]) - grayscale(img_last[y+1, x-1+k])) > PIXEL_THRESHOLD:
                                            filtercount += 1
                                    if abs(grayscale(img[y, x-1]) - grayscale(img_last[y, x-1])) > PIXEL_THRESHOLD:
                                        filtercount += 1
                                    if abs(grayscale(img[y, x+1]) - grayscale(img_last[y, x+1])) > PIXEL_THRESHOLD:
                                        filtercount += 1
                                    if filtercount < 4:
                                        count -= 1
                                        outcount += 1
                                    else:
                                        # FOR TESTING -- color pixel red in opencv
                                        for k in range(0, 3):
                                            for l in range(0, 3):
                                                img_draw[y+k, x+l] = [0, 0, 255]
                img_last = img

                if count > ALARM_THRESHOLD:
                    frames_since_thresh = 0
                    if not alarm:
                        alarm = True
                        # print("--- Writing to file")
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
                            # print("--- Closing file")
                            output.close()
                            base_timestamp = None 

                cv2.imshow("Video", img_draw)
                # print(count, outcount, "Alarm:", alarm)

            if alarm:
                if base_timestamp is not None:
                    packet.pts -= base_timestamp
                    packet.dts -= base_timestamp
                packet.stream = out_stream
                try:
                    output.mux(packet)
                except Exception as e:
                    print(e)

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

    if PIPE:
        os.close(pipe_fd)

if __name__ == '__main__':
    main()