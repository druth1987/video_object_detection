------------------------------------------------------------------------------------------------------------------------
Video Object Detection

------------------------------------------------------------------------------------------------------------------------
Overview

This project is a full backend service with an API that allows users to upload videos and search them for any object or
keyword quickly and efficiently.

It does this by first reading uploaded videos as individual frames. Users can then quickly search their video's frames
for anything, this is called zero shot object detection.

------------------------------------------------------------------------------------------------------------------------
Systems Design

Tech Used: Python, Flask, OpenCV, OWLv2, HuggingFace, SQLAlchemy, MSSQL, S3, Ubuntu, Celery, Redis, CUDA, Postman

Layers:

API: Flask WSGI server receives and validates requests then integrates with the other layers to formulate the correct
response.

Application: Ubuntu server with an asynchronous Celery task queue and CUDA GPU integration to execute resource heavy
image processing tasks. Frame comparison is done with ORB feature detection, FLANN based matching and Lowe's ratio. Only
frames that are sufficiently unique are saved. Frames are then searched with OWLv2, a self-training model that performs
zero shot object detection.

Database: MSSQL database that stores all user data and the status of uploads and searches. MSSQL integrates with the
API and Application layers through the SQLAlchemy ORM.

Object Storage: Video frames are saved in Amazon S3 object storage. The integration is handled with Boto3. Frames are
sent to the API and Application layers as presigned URLs.

------------------------------------------------------------------------------------------------------------------------
Setup

Database: Create MSSQL database and run database\mssql_script.sql to add tables

Object Storage: Add s3 bucket called movie-frames

Connections: Update connection variables in video_object_detection/connections.py

API:
    1. Install dependencies from api directory on API server
    2. Install video_object_detection package from project repository
    3. Download or create video_saves folder in same directory as flask_api.py
    4. Run flask_api.py

Application:
    1. Install Ubuntu 22.04 on application server
    2. Install redis at system level, add API server IP to redis.conf, start service
    3. In python venv install dependencies from application directory
    4. Install video_object_detection package from project repository in venv
    5. Start celery with: celery -A celery_app worker --loglevel=info -P eventlet

Testing: To use the sample postman calls in the test directory follow the steps below.
    1. Post to the users endpoint to receive an API key
    2. Add API key to the header for all following requests
    3. Attach mp4 file when posting to uploads

------------------------------------------------------------------------------------------------------------------------
Next Features

Video Streaming: Uploaded videos are temporarily saved in the video_saves folder on the API layer while they are
processed into frames. This allows failed uploads to be retried, but uses additional storage and requires the API and
Application layers to have access to the same video_saves folder.

A multimedia framework like FFmpeg would allow uploads to be streamed directly to the Application server for processing
without a local save. This would reduce storage, but prevent failed uploads from being retried and increase complexity.

Testing: System testing with Postman has been performed, but additional unit testing is required.

Deployment: Docker images would alloy the API and Application environments to be managed and deployed more efficiently.

Error Handling: Basic validation and rollbacks are present, but more robust error handling is required between layers.