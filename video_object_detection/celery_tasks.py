import os
from celery import shared_task
from video_object_detection import s3_api
from video_object_detection import sql_alchemy_queries
from video_object_detection import video_capture
from video_object_detection import frame_search
from video_object_detection import connections

# shared celery tasks called by async celery app

@shared_task()
def process_mov(uid, mid):
    status = 1  # SQL movie upload status, Null in progress (default), 0 error, 1 success
    try:
        video_capture.record_frames(uid, mid)
    except Exception as error:   # delete partial video upload frames from s3 and SQL
        status = 0
        s3_api.delete_movie(uid, mid)
        sql_alchemy_queries.delete_frames(mid)
        print(f"Upload error: {error}")
    os.remove(connections.video_saves_file_path + f'/video_saves/{uid}-{mid}.mp4')  # delete local video file
    sql_alchemy_queries.update_upload(mid, status)
    print(f"Upload Complete, Status: {status}")


@shared_task()
def search_mov(sid, uid, mid, word):
    status = 1  # SQL search status, Null in progress (default), 0 error, 1 success
    try:
        res = frame_search.frame_search(s3_api.get_frame_urls(uid, mid), word)  # returns s3 urls
        for url in res:
            sql_alchemy_queries.add_result(sid, url)
    except Exception as error:  # remove failed search SQL entries
        status = 0
        sql_alchemy_queries.delete_results(sid)
        print(f"Search error: {error}")
    sql_alchemy_queries.update_search(sid, status)
    print(f"Search Complete, Status: {status}")
