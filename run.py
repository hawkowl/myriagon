import toga
import toga.constants

from twisted.internet.cfreactor import install
install()

from twisted.internet import reactor, task
from twisted.python.filepath import FilePath

import attr
import cattr
import datetime
import appdirs
import json

from attr.validators import instance_of
from math import floor
from typing import List


@attr.s
class Task(object):
    id = attr.ib(validator=instance_of(int))
    name = attr.ib(validator=instance_of(str))
    budget_seconds = attr.ib(validator=instance_of(int))
    budget_per = attr.ib(validator=instance_of(str))
    cutoff = attr.ib(validator=instance_of(str))

@attr.s
class TimeSpent(object):
    started = attr.ib()
    finished = attr.ib()


WINDOW_WIDTH = 640
PADDING_WIDTH = 15

task_windows = {}


time_spent = {
    1: []
}


def load_tasks():

    dest = FilePath(appdirs.user_data_dir("myriagon", "hawkowl"))
    task_file = dest.child("tasks.json")

    if not task_file.exists():
        dest.makedirs(True)
        task_file.setContent(b"[]")

    return cattr.loads(
        json.loads(task_file.getContent().decode('utf8')),
        List[Task])


def save_tasks(tasks):

    dest = FilePath(appdirs.user_data_dir("myriagon", "hawkowl"))
    dest.makedirs(True)

    task_file = dest.child("tasks.json")
    task_file.setContent(json.dumps(cattr.dumps(tasks)).encode('utf8'))


def get_time_for_session(task):

    cd = datetime.date.today()
    cutoff_time = datetime.datetime(cd.year, cd.month, cd.day)

    if task.cutoff == "week":
        cutoff_delta = datetime.timedelta(days=datetime.datetime.isoweekday(cutoff_time))

    cutoff_time = cutoff_time - cutoff_delta

    time_spent_this_per = sum(map(
        lambda s: (s.finished - s.started).total_seconds(),
        filter(lambda t: t.started > cutoff_time,
               time_spent[task.id])))

    return time_spent_this_per



def get_time_needed_for_session(task):


    if task.cutoff == "week":
        if task.budget_per == "day":
            return task.budget_seconds * 7


def make_task_window(app, myr_task):

    if myr_task.id in task_windows.keys():
        task_windows[myr_task.id].show()
        return

    box = toga.Box()
    box.style.padding = PADDING_WIDTH

    timer_box = toga.Box()
    timer_box.style.flex_direction = "row"
    timer_box.style.justify_content = "center"

    needed = get_time_needed_for_session(myr_task)
    spent = [get_time_for_session(myr_task)]

    started = [0]

    timer_label = toga.Label("00:00", alignment=toga.constants.CENTER_ALIGNED)

    def update_label():
        if started[0]:
            total = needed - spent[0] + (started[0] - reactor.seconds())
        else:
            total = needed - spent[0]
        lab = "{:02d}:{:02d}:{:02d}".format(floor(total / 3600), floor((total % 3600) / 60), floor(total % 60))
        timer_label.text = lab

    update_label()

    button_box = toga.Box()
    box.add(timer_box)
    box.add(button_box)

    font = toga.Font("Helvetica", 90)

    timer_label.style.width = WINDOW_WIDTH - PADDING_WIDTH * 2
    timer_label.style.height = 120
    timer_label.set_font(font)
    timer_box.add(timer_label)

    button = toga.Button('Go go go')

    # lol scopign
    do_things = None
    loops = []

    def stop_things(btn):
        button.label = "Start"
        button.on_press = do_things

        time_spent[myr_task.id].append(TimeSpent(
            started=datetime.datetime.utcfromtimestamp(started[0]),
            finished=datetime.datetime.utcfromtimestamp(reactor.seconds())))

        started[0] = 0
        spent[0] = get_time_for_session(myr_task)

        while loops:
            loops.pop().stop()

    def dt(btn):
        started[0] = reactor.seconds()
        button.label = "Stop"
        button.on_press = stop_things

        lp = task.LoopingCall(update_label)
        lp.start(0.1)
        loops.append(lp)
    do_things = dt

    button.on_press = do_things
    button_box.add(button)

    window = toga.Window(title=myr_task.name, position=(150,150))
    window._set_title(myr_task.name)
    window.content = box
    window.show()

    task_windows[myr_task.id] = window


def make_add_task_window(app):
    pass


def build(app):

    tasks = [
        Task(id=1, name="Thing", budget_seconds=60, budget_per="day", cutoff="week"),
    ]
    save_tasks(tasks)

    tasks = load_tasks()

    box = toga.Box()
    box.style.padding = PADDING_WIDTH

    fullbox = toga.Box()
    fullbox.style.width = WINDOW_WIDTH - PADDING_WIDTH * 2

    itemlist = toga.ScrollContainer(horizontal=False, vertical=True)
    itemlist.style.height = 400
    itemlist.style.width = WINDOW_WIDTH - PADDING_WIDTH * 2
    box.add(itemlist)

    item_label_font = toga.Font("Helvetica", 18)

    for task in tasks:
        itembox = toga.Box()
        itembox.style.flex_direction = "row"

        lbl = toga.Label(task.name)
        lbl.style.width = (WINDOW_WIDTH - PADDING_WIDTH * 2) / 4 * 3
        lbl.set_font(item_label_font)

        btn = toga.Button("Open")
        btn.style.width = (WINDOW_WIDTH - PADDING_WIDTH * 2) / 4

        lbl.style.height = btn.style.height

        itembox.add(lbl)
        itembox.add(btn)
        btn.on_press = lambda _: make_task_window(app, task)
        fullbox.add(itembox)

    button_box = toga.Box()
    button = toga.Button('Add New Task')

    def open_new(t):
        window = make_add_task_window(app)

    button.on_press = open_new
    button_box.add(button)

    app.main_window.size = (100,100)

    itemlist.content = fullbox
    box.add(button_box)

    return box


if __name__ == '__main__':
    app = toga.App('Myriagon', 'net.atleastfornow.myriagon', startup=build)
    app.main_loop()
