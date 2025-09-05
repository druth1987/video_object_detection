from celery import Celery
from video_object_detection import celery_tasks  # have to import to access shared tasks, even if not used

# basic Ubuntu Celery app with redis message broker to run async shared tasks

cel_app = Celery('cel_app', broker='redis://localhost', backend='redis://localhost', task_ignore_result=True)
cel_app.set_default()  # sets app as current/default to use shared tasks
