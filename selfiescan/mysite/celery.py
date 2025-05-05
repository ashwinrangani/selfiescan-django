import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

celery_app = Celery("mysite")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()
celery_app.conf.worker_concurrency = 1  # Only process 1 tasks at a time

@celery_app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'check-expired-subscriptions-daily': {
        'task': 'photoapp.tasks.notify_expired_subscriptions',
        'schedule': crontab(hour=0, minute=0),  # Every day at midnight
    },
}
