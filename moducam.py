import av
import configparser
import collections
import threading
import queue
from datetime import datetime
import sys
import os
import argparse
import io
import imageio
import subprocess

MAX_PIPE_QUEUE = 10
CONFIG_ERROR = 5
FILENOTFOUND_ERROR = 6

def checkDirectory(path):
    if path != '':
        if path[-1] != '/':
            path += '/'
        if not os.path.exists(path):
            raise argparse.ArgumentTypeError(f"{path} is not a directory")
    return path

def setArgParams():
    global CONFIG_PATH, PIPE, VIDEO_DIRECTORY
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description='Start Moducam.')
    
    parser.add_argument('-c', '--config', type=str, help='Path to the configuration file', default=script_dir+'/config.ini')
    parser.add_argument('--pipe', action='store_true', help='Enable pipe mode')
    parser.add_argument('video_directory', type=checkDirectory, nargs='?', help='Destination video directory', default='')
    
    args = parser.parse_args()

    CONFIG_PATH = args.config
    PIPE = args.pipe
    VIDEO_DIRECTORY = args.video_directory

def setConfigurations():
    # Change this behavior?
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")
        exit(FILENOTFOUND_ERROR)

    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)

    global CAMERA_PATH, NAME, PIXEL_THRESHOLD, ALARM_THRESHOLD, PIXEL_STEP, \
        ZONE_POINTS, FRAMES_AFTER_ALARM, BUFFER_SIZE, \
        RUN_ON_ALARM, RUN_ON_ALARM_END

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

    config_runonalarm = config['Scripts']['run_on_alarm']
    config_runonalarmend = config['Scripts']['run_on_alarm_end']
    RUN_ON_ALARM = list(eval(config_runonalarm)) if config_runonalarm else None
    RUN_ON_ALARM_END = list(eval(config_runonalarmend)) if config_runonalarmend else None

def grayscale(pxl):
    return 0.299*pxl[0] + 0.587*pxl[1] + 0.114*pxl[2]

def getOutFileName():
    return VIDEO_DIRECTORY + datetime.now().strftime(NAME + '-%Y-%m-%d_%H-%M-%S') + '.mp4'

def compute_zone(points, width, height):
    if len(points) > 0:
        if points[0] != points[-1]:
            points.append(points[0])
        if len(points) < 4:
            print("ERROR: Zone cannot be defined by less than 3 points", file=sys.stderr)
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
            print("ERROR: Row has odd number of intercepts:", file=sys.stderr)
            print(intercepts, file=sys.stderr)
            exit(-1)
        
        intercepts.sort()

        # Couple up x-intercepts for this row to make tuple ranges
        row_ranges = []
        for i in range(0, len(intercepts), 2):
            row_ranges.append( (intercepts[i], intercepts[i+1]) )

        ranges.append(row_ranges)
    return ranges

def pixelPass(img, img_last, scan_ranges, img_draw):
    count = 0
    if img_last is not None:
        for y in range(0, len(scan_ranges), PIXEL_STEP):
            for r in scan_ranges[y]:
                for x in range(r[0], r[1], PIXEL_STEP):
                    # First step: Pixel color check
                    if abs(grayscale(img[y, x]) - grayscale(img_last[y, x])) > PIXEL_THRESHOLD:
                        count += 1
                        # Second step: Filter pixel by checking surrounding area
                        if filterPass(img, img_last, x, y) < 4:
                            count -= 1
                        else:
                            # FOR TESTING -- color pixel red in opencv
                            for k in range(-1, 2):
                                for l in range(0, 3):
                                    img_draw[y+k, x+l] = [255, 0, 0]
    return count

def filterPass(img, img_last, x, y):
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
    return filtercount

def write_to_pipe(path, pipe_queue):
    with open(path, 'wb') as pipe:
        while True:
            data = pipe_queue.get()
            if data is None:
                break
            
            img_stream = io.BytesIO()
            imageio.imwrite(img_stream, data, format='JPEG')
            image_data = img_stream.getvalue()

            sys.stdout.buffer.write(image_data)
            sys.stdout.buffer.flush()
            pipe_queue.task_done()

def main():
    setArgParams()
    try:
        setConfigurations()
    except Exception as e:
        print(e, file=sys.stderr)
        exit(CONFIG_ERROR)

    points = ZONE_POINTS

    video = av.open(CAMERA_PATH, 'r', options={'rtsp_transport':'tcp'}, timeout=(10, 12))
    in_stream = video.streams.video[0]

    output = None
    out_stream = None
    base_timestamp = None  # Stores the first timestamp when alarm triggers
    fake_timestamp = 0  # Made up timestamp to increment when one doesn't exist
    ts_incr = (1 / 30) / in_stream.time_base # How much to increment fake ts

    alarm = False
    frames_since_thresh = 0
    img_last = None

    buffer = collections.deque()

    scan_ranges = compute_zone(points, in_stream.width, in_stream.height)
    
    framecount = 0
    if PIPE:
        pipe_path = 'my_pipe'
        pipe_queue = queue.Queue()
        worker_thread = threading.Thread(target=write_to_pipe, args=(pipe_path, pipe_queue))
        worker_thread.daemon = True
        worker_thread.start()

    try:
        for packet in video.demux(in_stream):
            for frame in packet.decode():
                img = frame.to_ndarray(format='rgb24')

                img_draw = img.copy()

                count = pixelPass(img, img_last, scan_ranges, img_draw)
                img_last = img

                if count > ALARM_THRESHOLD:
                    frames_since_thresh = 0
                    if not alarm:
                        alarm = True
                        # print("--- Writing to file")
                        fake_timestamp = 0
                        output = av.open(getOutFileName(), 'w', format='mp4')
                        out_stream = output.add_stream(template=in_stream)

                        # base_timestamp = buffer[0].pts if len(buffer) and buffer[0].pts else 0

                        for p in buffer:
                            if base_timestamp is None:
                                if p.pts:
                                    base_timestamp = p.pts - fake_timestamp
                                elif p.dts:
                                    base_timestamp = p.pts - fake_timestamp
                                else:
                                    p.pts = fake_timestamp
                                    p.dts = fake_timestamp
                                    fake_timestamp += ts_incr
                            if p.pts:
                                p.pts -= base_timestamp
                            if p.dts:
                                p.dts -= base_timestamp
                            p.stream = out_stream
                            try:
                                output.mux(p)
                            except Exception as e:
                                print(e, file=sys.stderr)
                                exit(7)
                        buffer.clear()

                        if RUN_ON_ALARM:
                            subprocess.Popen(RUN_ON_ALARM, stdout=subprocess.DEVNULL)
                    
                else:
                    frames_since_thresh += 1
                    if alarm:
                        if frames_since_thresh > FRAMES_AFTER_ALARM and alarm:
                            alarm = False
                            # print("--- Closing file")
                            fake_timestamp = 0
                            output.close()
                            base_timestamp = None
                            
                            if RUN_ON_ALARM_END:
                                subprocess.Popen(RUN_ON_ALARM_END, stdout=subprocess.DEVNULL)

                # print(count, "Alarm:", alarm)
                framecount += 1
                if PIPE and pipe_queue.qsize() < MAX_PIPE_QUEUE and framecount % 2 == 0:
                    pipe_queue.put(img_draw)

            if alarm:
                if base_timestamp is None:
                    if packet.pts:
                        base_timestamp = packet.pts
                    elif packet.dts:
                        base_timestamp = packet.pts
                    else:
                        packet.dts = fake_timestamp
                        packet.pts = fake_timestamp
                        fake_timestamp += ts_incr
                if packet.pts:
                    packet.pts -= base_timestamp
                if packet.dts:
                    packet.dts -= base_timestamp
                packet.stream = out_stream
                try:
                    output.mux(packet)
                except Exception as e:
                    print(e, file=sys.stderr)
                    exit(7)

            else:
                if len(buffer) == BUFFER_SIZE:
                    buffer.popleft()

                if packet.pts is not None:
                    buffer.append(packet)
            
    except KeyboardInterrupt:
        pass

    if PIPE:
        pipe_queue.put(None)
        worker_thread.join()

if __name__ == '__main__':
    main()
