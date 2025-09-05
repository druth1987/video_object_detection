import boto3
import cv2
from video_object_detection import connections

# AWS s3 integration functions

s3 = boto3.client('s3',
                  aws_access_key_id=connections.aws_access_key_id,
                  aws_secret_access_key=connections.aws_secret_access_key)

cors_config = {  # allows apache through CORS to download s3 pre-signed URLs for front end testing
    'CORSRules': [{
        'AllowedMethods': ['GET', 'POST', 'DELETE'],
        'AllowedOrigins': ["http://127.0.0.1"]  # apache IP address
    }]
}

s3.put_bucket_cors(Bucket="movie-frames", CORSConfiguration=cors_config)


# all functions accept and use SQL keys, not user emails/movie names
def get_frame_urls(uid, mid):
    frames = s3.list_objects(Bucket='movie-frames', Prefix=f'{uid}/{mid}')['Contents']
    res = []
    for f in frames:  # urls expire in 1 hour by default
        res.append(s3.generate_presigned_url(ClientMethod='get_object',  # key = s3 bucket file name (inc flat path)
                                             Params={'Bucket': 'movie-frames', 'Key': f['Key']}))
    return res


def get_movie(uid, mid):
    frames = s3.list_objects(Bucket='movie-frames', Prefix=f'{uid}/{mid}')['Contents']
    for f in frames:
        file_name = f['Key'].split('/', 2)[2]  # removes s3 prefix
        s3.download_file(Bucket='movie-frames', Key=f['Key'], Filename=file_name)  # s3 key, local filename


def image_upload(img, uid, mid, fid):  # takes numpy.ndarray img file
    # imencode compresses/saves img as jpeg in memory @ 90% compression w/ 100 max quality
    # s3 put_object only accepts bytes or bytearray, not ndarray
    # can't use s3 upload object b/c it must be file object with read
    img = cv2.imencode('.jpeg', img, [cv2.IMWRITE_JPEG_QUALITY, 100])[1]
    s3.put_object(Bucket='movie-frames', Body=img.tobytes(), Key=f'{uid}/{mid}/{fid}.jpeg')


def delete_movie(uid, mid):
    frames = s3.list_objects(Bucket='movie-frames', Prefix=f'{uid}/{mid}')['Contents']
    for f in frames:
        s3.delete_object(Bucket='movie-frames', Key=f['Key'])
