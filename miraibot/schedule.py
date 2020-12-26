"""
# **各种范例**
## 运行范例
>>> import time
>>> def job():
>>>     times = time.strftime("%Y-%m-%d %a %H:%M:%S ", time.localtime())
>>>     print(f"\r现在时间是： {times}", end='')

>>> schedule.every(10).minutes.do(job)               # 每隔 10 分钟运行一次 job 函数
>>> schedule.every().hour.do(job)                    # 每隔 1 小时运行一次 job 函数
>>> schedule.every().day.at("10:30").do(job)         # 每天在 10:30 时间点运行 job 函数
>>> schedule.every().monday.do(job)                  # 每周一 运行一次 job 函数
>>> schedule.every().wednesday.at("13:15").do(job)   # 每周三 13：15 时间点运行 job 函数
>>> schedule.every().minute.at(":17").do(job)        # 每分钟的 17 秒时间点运行 job 函数

>>> try:
>>>     while True:
>>>         schedule.run_pending()
>>>         time.sleep(0.2)
>>> except KeyboardInterrupt:
>>>     pass



## 只跑一次的任务
>>> def job_that_executes_once():
>>>     # Do some work ...
>>>     return schedule.CancelJob

>>> schedule.every().day.at('22:30').do(job_that_executes_once)



## 取消多个任务
>>> # 通过 tag 函数给它们添加唯一标识符进行分组，取消时通过标识符进行取消相应组的任务
>>> def greet(name):
>>>     print('Hello {}'.format(name))

>>> schedule.every().day.do(greet, 'Andrea').tag('daily-tasks', 'friend')
>>> schedule.every().hour.do(greet, 'John').tag('hourly-tasks', 'friend')
>>> schedule.every().hour.do(greet, 'Monica').tag('hourly-tasks', 'customer')
>>> schedule.every().day.do(greet, 'Derek').tag('daily-tasks', 'guest')

>>> schedule.clear('daily-tasks')



## 给任务传递函数
>>> def greet(name):
>>>     print('Hello', name)

>>> schedule.every(2).seconds.do(greet, name='Alice')
>>> schedule.every(4).seconds.do(greet, name='Bob')


# **说明**
目前该调度器暂时不处理任何异常，一旦发生异常会导致整个调度器挂掉。
因此建议在使用时充分考虑各种情况。

具体信息也可以在 https://github.com/dbader/schedule 上查看
想要更详细的使用方法? 推荐看看 https://www.jianshu.com/p/57d09d3c8998
"""

from .log import logger

import collections
import datetime
import functools
import random
import re
import time
import asyncio
import traceback


class ScheduleError(Exception):
    """基本时间表例外"""
    pass


class ScheduleValueError(ScheduleError):
    """基本计划值错误"""
    pass


class IntervalError(ScheduleValueError):
    """使用了不正确的间隔"""
    pass


class CancelJob(object):
    """
    可以从作业中返回以取消计划本身。
    """
    pass


class Scheduler(object):
    """
    Objects instantiated by the :class:`Scheduler <Scheduler>` are
    factories to create jobs, keep record of scheduled jobs and
    handle their execution.
    """
    def __init__(self):
        self.jobs = []

    async def run_pending(self):
        """
        运行计划运行的所有作业。

        Please note that it is *intended behavior that run_pending()
        does not run missed jobs*. For example, if you've registered a job
        that should run every minute and you only call run_pending()
        in one hour increments then your job won't be run 60 times in
        between but only once.
        """
        runnable_jobs = (job for job in self.jobs if job.should_run)
        for job in sorted(runnable_jobs):
            await self._run_job(job)

    async def run_all(self, delay_seconds=0):
        """
        运行所有作业，无论它们是否计划运行。

        每个作业之间增加了 `delay` 秒的延迟。 这有助于随着时间的推移更均匀地分配作业生成的系统负载。

        :param delay_seconds: 每个执行的作业之间增加了延迟
        """
        logger.debug(f'Running *all* %i jobs with %is delay inbetween {len(self.jobs)} {delay_seconds}')
        for job in self.jobs[:]:
            await self._run_job(job)
            await asyncio.sleep(delay_seconds)

    def clear(self, tag=None):
        """
        删除标有给定标签的计划作业，或者如果省略标签则删除所有作业。

        :param tag: 用于标识要删除的作业子集的标识符
        """
        if tag is None:
            del self.jobs[:]
        else:
            self.jobs[:] = (job for job in self.jobs if tag not in job.tags)

    def cancel_job(self, job):
        """
        删除计划的作业。

        :param job: 计划外的工作
        """
        try:
            self.jobs.remove(job)
        except ValueError:
            pass

    def every(self, interval=1):
        """
        安排新的定期工作。

        :param interval: 一定时间单位的数量
        :return: An unconfigured :class:`Job <Job>`
        """
        job = Job(interval, self)
        return job

    async def _run_job(self, job):
        try:
            ret = await job.run()
            if isinstance(ret, CancelJob) or ret is CancelJob:
                self.cancel_job(job)
        except:
            logger.error(traceback.format_exc())

    @property
    def next_run(self):
        """
        下一个作业应运行的日期时间。

        :return: A :class:`~datetime.datetime` object
        """
        if not self.jobs:
            return None
        return min(self.jobs).next_run

    @property
    def idle_seconds(self):
        """
        :return: Number of seconds until
                 :meth:`next_run <Scheduler.next_run>`.
        """
        return (self.next_run - datetime.datetime.now()).total_seconds()


class Job(object):
    """
    A periodic job as used by :class:`Scheduler`.

    :param interval: A quantity of a certain time unit
    :param scheduler: The :class:`Scheduler <Scheduler>` instance that
                      this job will register itself with once it has
                      been fully configured in :meth:`Job.do()`.

    Every job runs at a given fixed time interval that is defined by:

    * a :meth:`time unit <Job.second>`
    * a quantity of `time units` defined by `interval`

    A job is usually created and returned by :meth:`Scheduler.every`
    method, which also defines its `interval`.
    """
    def __init__(self, interval, scheduler=None):
        self.interval = interval  # pause interval * unit between runs
        self.latest = None  # upper limit to the interval
        self.job_func = None  # the job job_func to run
        self.unit = None  # time units, e.g. 'minutes', 'hours', ...
        self.at_time = None  # optional time at which this job runs
        self.last_run = None  # datetime of the last run
        self.next_run = None  # datetime of the next run
        self.period = None  # timedelta between runs, only valid for
        self.start_day = None  # Specific day of the week to start on
        self.tags = set()  # unique set of tags for the job
        self.scheduler = scheduler  # scheduler to register with

    def __lt__(self, other):
        """定期作业可以根据其下次运行的计划时间进行排序。
        PeriodicJobs are sortable based on the scheduled time they
        run next.
        """
        return self.next_run < other.next_run

    def __repr__(self):
        def format_time(t):
            return t.strftime('%Y-%m-%d %H:%M:%S') if t else '[never]'

        timestats = '(last run: %s, next run: %s)' % (
                    format_time(self.last_run), format_time(self.next_run))

        if hasattr(self.job_func, '__name__'):
            job_func_name = self.job_func.__name__
        else:
            job_func_name = repr(self.job_func)
        args = [repr(x) for x in self.job_func.args]
        kwargs = ['%s=%s' % (k, repr(v))
                  for k, v in self.job_func.keywords.items()]
        call_repr = job_func_name + '(' + ', '.join(args + kwargs) + ')'

        if self.at_time is not None:
            return 'Every %s %s at %s do %s %s' % (
                   self.interval,
                   self.unit[:-1] if self.interval == 1 else self.unit,
                   self.at_time, call_repr, timestats)
        else:
            fmt = (
                'Every %(interval)s ' +
                ('to %(latest)s ' if self.latest is not None else '') +
                '%(unit)s do %(call_repr)s %(timestats)s'
            )

            return fmt % dict(
                interval=self.interval,
                latest=self.latest,
                unit=(self.unit[:-1] if self.interval == 1 else self.unit),
                call_repr=call_repr,
                timestats=timestats
            )

    @property
    def second(self):
        if self.interval != 1:
            raise IntervalError('用 seconds 而不是 second')
        return self.seconds

    @property
    def seconds(self):
        self.unit = 'seconds'
        return self

    @property
    def minute(self):
        if self.interval != 1:
            raise IntervalError('用 minutes 而不是 minute')
        return self.minutes

    @property
    def minutes(self):
        self.unit = 'minutes'
        return self

    @property
    def hour(self):
        if self.interval != 1:
            raise IntervalError('用 hours 代替 hour')
        return self.hours

    @property
    def hours(self):
        self.unit = 'hours'
        return self

    @property
    def day(self):
        if self.interval != 1:
            raise IntervalError('用 days 代替 day')
        return self.days

    @property
    def days(self):
        self.unit = 'days'
        return self

    @property
    def week(self):
        if self.interval != 1:
            raise IntervalError('用 weeks 代替 week')
        return self.weeks

    @property
    def weeks(self):
        self.unit = 'weeks'
        return self

    @property
    def monday(self):
        if self.interval != 1:
            raise IntervalError('用 mondays 代替 monday')
        self.start_day = 'monday'
        return self.weeks

    @property
    def tuesday(self):
        if self.interval != 1:
            raise IntervalError('用 tuesdays 代替 tuesday')
        self.start_day = 'tuesday'
        return self.weeks

    @property
    def wednesday(self):
        if self.interval != 1:
            raise IntervalError('用 wednesdays 代替 wednesday')
        self.start_day = 'wednesday'
        return self.weeks

    @property
    def thursday(self):
        if self.interval != 1:
            raise IntervalError('用 thursdays 代替 thursday')
        self.start_day = 'thursday'
        return self.weeks

    @property
    def friday(self):
        if self.interval != 1:
            raise IntervalError('用 fridays 代替 friday')
        self.start_day = 'friday'
        return self.weeks

    @property
    def saturday(self):
        if self.interval != 1:
            raise IntervalError('用 saturdays 代替 saturday')
        self.start_day = 'saturday'
        return self.weeks

    @property
    def sunday(self):
        if self.interval != 1:
            raise IntervalError('用 sundays 代替 sunday')
        self.start_day = 'sunday'
        return self.weeks

    def tag(self, *tags):
        """
        用一个或多个唯一标识符标记作业。

        标签必须是可哈希的。 重复的标签将被丢弃。

        :param tags: A unique list of ``Hashable`` tags.
        :return: The invoked job instance
        """
        if not all(isinstance(tag, collections.Hashable) for tag in tags):
            raise TypeError('Tags must be hashable')
        self.tags.update(tags)
        return self

    def at(self, time_str):
        """
        指定运行作业的特定时间。

        :param time_str: A string in one of the following formats: `HH:MM:SS`,
            `HH:MM`,`:MM`, `:SS`. The format must make sense given how often
            the job is repeating; for example, a job that repeats every minute
            should not be given a string in the form `HH:MM:SS`. The difference
            between `:MM` and `:SS` is inferred from the selected time-unit
            (e.g. `every().hour.at(':30')` vs. `every().minute.at(':30')`).
        :return: The invoked job instance
        """
        if (self.unit not in ('days', 'hours', 'minutes')
                and not self.start_day):
            raise ScheduleValueError('Invalid unit')
        if not isinstance(time_str, str):
            raise TypeError('at() should be passed a string')
        if self.unit == 'days' or self.start_day:
            if not re.match(r'^([0-2]\d:)?[0-5]\d:[0-5]\d$', time_str):
                raise ScheduleValueError('Invalid time format')
        if self.unit == 'hours':
            if not re.match(r'^([0-5]\d)?:[0-5]\d$', time_str):
                raise ScheduleValueError(('Invalid time format for'
                                          ' an hourly job'))
        if self.unit == 'minutes':
            if not re.match(r'^:[0-5]\d$', time_str):
                raise ScheduleValueError(('Invalid time format for'
                                          ' a minutely job'))
        time_values = time_str.split(':')
        if len(time_values) == 3:
            hour, minute, second = time_values
        elif len(time_values) == 2 and self.unit == 'minutes':
            hour = 0
            minute = 0
            _, second = time_values
        else:
            hour, minute = time_values
            second = 0
        if self.unit == 'days' or self.start_day:
            hour = int(hour)
            if not (0 <= hour <= 23):
                raise ScheduleValueError('Invalid number of hours')
        elif self.unit == 'hours':
            hour = 0
        elif self.unit == 'minutes':
            hour = 0
            minute = 0
        minute = int(minute)
        second = int(second)
        self.at_time = datetime.time(hour, minute, second)
        return self

    def to(self, latest):
        """
        安排作业以不规则（随机）间隔运行。

        The job's interval will randomly vary from the value given
        to  `every` to `latest`. The range defined is inclusive on
        both ends. For example, `every(A).to(B).seconds` executes
        the job function every N seconds such that A <= N <= B.

        :param latest: 随机作业运行之间的最大间隔
        :return: 调用的作业实例
        """
        self.latest = latest
        return self

    def do(self, job_func, *args, **kwargs):
        """
        指定每次作业运行时应调用的 job_func 。

        作业运行时，所有其他参数都会传递给 job_func 。

        :param job_func: 预定功能
        :return: 调用的作业实例
        """
        self.job_func = functools.partial(job_func, *args, **kwargs)
        try:
            functools.update_wrapper(self.job_func, job_func)
        except AttributeError:
            # job_funcs already wrapped by functools.partial won't have
            # __name__, __module__ or __doc__ and the update_wrapper()
            # call will fail.
            pass
        self._schedule_next_run()
        self.scheduler.jobs.append(self)
        return self

    @property
    def should_run(self):
        """
        :return: ``True`` if the job should be run now.
        """
        return datetime.datetime.now() >= self.next_run

    def run(self):
        """
        运行该作业，然后立即重新计划它。

        :return: 由 `job_func` 返回的返回值
        """
        #logger.info(f'Running job %s {self}')
        ret = self.job_func()
        self.last_run = datetime.datetime.now()
        self._schedule_next_run()
        return ret

    def _schedule_next_run(self):
        """
        计算下一次应执行此作业的时刻。
        """
        if self.unit not in ('seconds', 'minutes', 'hours', 'days', 'weeks'):
            raise ScheduleValueError('Invalid unit')

        if self.latest is not None:
            if not (self.latest >= self.interval):
                raise ScheduleError('`latest` is greater than `interval`')
            interval = random.randint(self.interval, self.latest)
        else:
            interval = self.interval

        self.period = datetime.timedelta(**{self.unit: interval})
        self.next_run = datetime.datetime.now() + self.period
        if self.start_day is not None:
            if self.unit != 'weeks':
                raise ScheduleValueError('`unit` should be \'weeks\'')
            weekdays = (
                'monday',
                'tuesday',
                'wednesday',
                'thursday',
                'friday',
                'saturday',
                'sunday'
            )
            if self.start_day not in weekdays:
                raise ScheduleValueError('无效的开始日期')
            weekday = weekdays.index(self.start_day)
            days_ahead = weekday - self.next_run.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            self.next_run += datetime.timedelta(days_ahead) - self.period
        if self.at_time is not None:
            if (self.unit not in ('days', 'hours', 'minutes')
                    and self.start_day is None):
                raise ScheduleValueError(('Invalid unit without'
                                          ' specifying start day'))
            kwargs = {
                'second': self.at_time.second,
                'microsecond': 0
            }
            if self.unit == 'days' or self.start_day is not None:
                kwargs['hour'] = self.at_time.hour
            if self.unit in ['days', 'hours'] or self.start_day is not None:
                kwargs['minute'] = self.at_time.minute
            self.next_run = self.next_run.replace(**kwargs)
            # If we are running for the first time, make sure we run
            # at the specified time *today* (or *this hour*) as well
            if not self.last_run:
                now = datetime.datetime.now()
                if (self.unit == 'days' and self.at_time > now.time() and
                        self.interval == 1):
                    self.next_run = self.next_run - datetime.timedelta(days=1)
                elif self.unit == 'hours' \
                        and self.at_time.minute > now.minute \
                        or (self.at_time.minute == now.minute
                            and self.at_time.second > now.second):
                    self.next_run = self.next_run - datetime.timedelta(hours=1)
                elif self.unit == 'minutes' \
                        and self.at_time.second > now.second:
                    self.next_run = self.next_run - \
                                    datetime.timedelta(minutes=1)
        if self.start_day is not None and self.at_time is not None:
            # Let's see if we will still make that time we specified today
            if (self.next_run - datetime.datetime.now()).days >= 7:
                self.next_run -= self.period


# The following methods are shortcuts for not having to
# create a Scheduler instance:

#: Default :class:`Scheduler <Scheduler>` object
default_scheduler = Scheduler()

#: Default :class:`Jobs <Job>` list
jobs = default_scheduler.jobs  # todo: should this be a copy, e.g. jobs()?


def every(interval=1):
    """Calls :meth:`every <Scheduler.every>` on the
    :data:`default scheduler instance <default_scheduler>`.
    """
    return default_scheduler.every(interval)


async def run_pending():
    """Calls :meth:`run_pending <Scheduler.run_pending>` on the
    :data:`default scheduler instance <default_scheduler>`.
    """
    while True:
        await default_scheduler.run_pending()
        await asyncio.sleep(1)
        


async def run_all(delay_seconds=0):
    """Calls :meth:`run_all <Scheduler.run_all>` on the
    :data:`default scheduler instance <default_scheduler>`.
    """
    await default_scheduler.run_all(delay_seconds=delay_seconds)


def clear(tag=None):
    """Calls :meth:`clear <Scheduler.clear>` on the
    :data:`default scheduler instance <default_scheduler>`.
    """
    default_scheduler.clear(tag)


def cancel_job(job):
    """Calls :meth:`cancel_job <Scheduler.cancel_job>` on the
    :data:`default scheduler instance <default_scheduler>`.
    """
    default_scheduler.cancel_job(job)


def next_run():
    """Calls :meth:`next_run <Scheduler.next_run>` on the
    :data:`default scheduler instance <default_scheduler>`.
    """
    return default_scheduler.next_run


def idle_seconds():
    """Calls :meth:`idle_seconds <Scheduler.idle_seconds>` on the
    :data:`default scheduler instance <default_scheduler>`.
    """
    return default_scheduler.idle_seconds
