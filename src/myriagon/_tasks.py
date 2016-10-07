import attr
import cattr
import appdirs
import json

from typing import List
from attr.validators import instance_of

from twisted.python.filepath import FilePath

from ._time import (
    load_time_spent,
    get_time_for_session, get_time_needed_for_session,
)


@attr.s
class Task(object):
    id = attr.ib(validator=instance_of(int))
    name = attr.ib(validator=instance_of(str))
    budget_seconds = attr.ib(validator=instance_of(int))
    budget_per = attr.ib(validator=instance_of(str))
    cutoff = attr.ib(validator=instance_of(str))
    since = attr.ib(validator=instance_of(int))


def load_tasks():

    dest = FilePath(appdirs.user_data_dir("myriagon", "hawkowl"))
    task_file = dest.child("tasks.json")

    if not task_file.exists():
        dest.makedirs(True)
        task_file.setContent(b"[]")

    loaded = cattr.loads(
        json.loads(task_file.getContent().decode('utf8')),
        List[Task])

    def sort(x):
        time = load_time_spent(x)
        return get_time_needed_for_session(x) - get_time_for_session(x, time)

    loaded.sort(key=sort, reverse=True)
    return loaded


def save_tasks(tasks):

    dest = FilePath(appdirs.user_data_dir("myriagon", "hawkowl"))
    dest.makedirs(True)

    task_file = dest.child("tasks.json")
    task_file.setContent(json.dumps(cattr.dumps(tasks)).encode('utf8'))
