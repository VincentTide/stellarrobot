from datetime import timedelta

BROKER_URL = 'amqp://guest:guest@localhost:5672//'

CELERY_IMPORTS = ('proj.tasks',)

CELERY_TIMEZONE = 'UTC'

CELERYBEAT_SCHEDULE = {
    'pending_payments': {
        'task': 'proj.tasks.pending_payments',
        'schedule': timedelta(seconds=90)
    }
}
