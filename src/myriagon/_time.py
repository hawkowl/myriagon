import attr
import cattr
import datetime
import appdirs
import json

from pytz import reference
from uuid import uuid4
from attr.validators import instance_of
from typing import List
from math import floor

from twisted.python.filepath import FilePath

from ._trash import get_days_in_month


@attr.s
class TimeSpent(object):
    started = attr.ib(validator=instance_of(int))
    finished = attr.ib(validator=instance_of(int))
    uuid = attr.ib(default=uuid4().hex,
                   validator=instance_of(str))


def seconds_into_clock(total):

    if total < 0:
        prefix = "-"
        total = -total
    else:
        prefix = ""

    return "{}{:02d}:{:02d}:{:02d}".format(
        prefix, floor(total / 3600),
        floor((total % 3600) / 60),
        floor(total % 60))


def seconds_into_iso8601(sec):

    time = datetime.datetime.utcfromtimestamp(sec).replace(tzinfo=pytz.utc).astimezone(reference.LocalTimezone())
    return time.isoformat()

def load_time_spent(task):

    dest = FilePath(appdirs.user_data_dir("myriagon", "hawkowl")).child("time")
    dest.makedirs(True)

    task_time_file = dest.child(str(task.id) + ".json")

    if not task_time_file.exists():
        dest.makedirs(True)
        task_time_file.setContent(b"[]")

    return cattr.loads(
        json.loads(task_time_file.getContent().decode('utf8')),
        List[TimeSpent])


def save_time_spent(task, time):

    dest = FilePath(appdirs.user_data_dir("myriagon", "hawkowl")).child("time")
    dest.makedirs(True)

    task_time_file = dest.child(str(task.id) + ".json")
    task_time_file.setContent(json.dumps(cattr.dumps(time)).encode('utf8'))


def get_time_for_session(task, time):

    cd = datetime.date.today()

    if task.cutoff == "week":

        cutoff_time = datetime.datetime(cd.year, cd.month, cd.day)
        cutoff_delta = datetime.timedelta(
            days=datetime.datetime.weekday(cutoff_time))

        cutoff_time = (cutoff_time - cutoff_delta).timestamp()

    elif task.cutoff == "month":
        cutoff_time = datetime.datetime(cd.year, cd.month, 1).timestamp()

    qualifiers = filter(lambda t: t.started > cutoff_time, time)
    time_spent_this_per = sum(map(
        lambda s: s.finished - s.started, qualifiers))

    return time_spent_this_per


def get_time_needed_for_session(task):

    cd = datetime.date.today()
    cutoff_time = datetime.datetime(cd.year, cd.month, cd.day)

    if task.cutoff == "week":
        cutoff_delta = cutoff_time - datetime.timedelta(
            days=datetime.datetime.weekday(cutoff_time))

        if task.since > cutoff_delta.timestamp():
            days = 7 - datetime.datetime.weekday(cutoff_time)
        else:
            days = 7

        if task.budget_per == "day":
            return task.budget_seconds * days
        elif task.budget_per == "week":
            return task.budget_seconds
        elif task.budget_per == "month":
            return task.budget_seconds / 4  # 4 weeks in a month rite

    if task.cutoff == "month":

        days_in_month = get_days_in_month(cd.year, cd.month)
        cutoff_delta = datetime.datetime(cd.year, cd.month, 1)

        if task.since > cutoff_delta.timestamp():
            days = days_in_month - cd.day + 1
        else:
            days = days_in_month

        if task.budget_per == "day":
            return task.budget_seconds * days

        elif task.budget_per == "week":
            return days // 7 * task.budget_seconds

        elif task.budget_per == "month":
            return task.budget_seconds
