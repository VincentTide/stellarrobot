from __future__ import absolute_import

from celery import Celery

celery = Celery('proj')
celery.config_from_object('proj.celeryconfig')
