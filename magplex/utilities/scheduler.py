import logging
from datetime import timezone

from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from magplex.utilities import tasks
from magplex.utilities.localization import Locale
from magplex.utilities.variables import Environment


def wake_scheduler():
    """This job is responsible for keeping the scheduler alive, for when tasks are manually triggered."""
    pass


class IgnoreWakeSchedulerFilter(logging.Filter):
    def filter(self, record):
        return "wake_scheduler" not in record.getMessage()


logging.getLogger("apscheduler.executors.default").addFilter(IgnoreWakeSchedulerFilter())


class TaskManager:
    _scheduler = None

    @classmethod
    def create_scheduler(cls):
        if cls._scheduler is None:
            cls._scheduler = BackgroundScheduler(
                jobstores={
                    'default': RedisJobStore(
                        host=Environment.REDIS_HOST,
                        port=Environment.REDIS_PORT,
                        db=1
                    )
                },
                job_defaults={
                    'misfire_grace_time': 30,
                    'coalesce': True,
                    'max_instances': 1
                },
                timezone=timezone.utc
            )
            cls._scheduler.add_job(wake_scheduler, 'interval', id="wake_scheduler",
                                   seconds=5, replace_existing=True)
            logging.info(Locale.TASK_JOB_ADDED_SUCCESSFULLY)

        return cls._scheduler

    @classmethod
    def start(cls):
        if cls._scheduler is not None and not cls._scheduler.running:
            cls._scheduler.start()

    @classmethod
    def get_scheduler(cls):
        if cls._scheduler is None:
            cls.create_scheduler()
        return cls._scheduler
