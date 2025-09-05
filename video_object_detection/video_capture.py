import cv2
import math
from video_object_detection import s3_api
from video_object_detection import sql_alchemy_queries
from video_object_detection import frame_comparison
from video_object_detection import connections


# called by Celery asynchronous task queue on Ubuntu application server
# saves the uploaded video, then processes it as individual frames
# parses at 1 fps to increase performance and reduce storage without losing accuracy
# uploads distinct frames to s3 object storage and updates SQL


def record_frames(uid, mid):  # SQL user id, and movie id
    mov = cv2.VideoCapture(connections.video_saves_file_path + f'/video_saves/{uid}-{mid}.mp4')
    fps = math.ceil(mov.get(cv2.CAP_PROP_FPS))  # round up fps
    ctr = 0  # frame counter
    prev_frame, dif_frame = None, True

    while True:
        playing, cur_frame = mov.read()  # reads current frame as a color numpy.ndarray
        if not playing:
            break
        if ctr > 0:
            dif_frame = frame_comparison.dif_frame(prev_frame, cur_frame)
        if dif_frame:
            s3_api.image_upload(cur_frame, uid, mid, ctr)
            sql_alchemy_queries.add_frame(mid, ctr)
            prev_frame = cur_frame
        ctr += fps
        mov.set(cv2.CAP_PROP_POS_FRAMES, ctr)  # fast-forward ~1 second
    print('Frames recorded')
