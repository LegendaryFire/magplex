import zoneinfo

from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from magplex.utilities.environment import Variables


class TaskManager:
    _scheduler = None

    @classmethod
    def create_scheduler(cls):
        if cls._scheduler is None:
            cls._scheduler = BackgroundScheduler(
                jobstores={
                    'default': RedisJobStore(
                        host=Variables.REDIS_HOST,
                        port=Variables.REDIS_PORT,
                        db=1
                    )
                },
                timezone=zoneinfo.ZoneInfo(Variables.STB_TIMEZONE)
            )
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