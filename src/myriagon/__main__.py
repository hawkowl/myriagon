import toga
import toga.constants

from twisted.python.runtime import platform

if platform.isMacOSX():
    DISPLAY_FONT = "Helvetica Light"
    from twisted.internet.cfreactor import install
    install()
elif platform.isLinux():
    DISPLAY_FONT = "Ubuntu Light"
    from twisted.internet.gireactor import install
    install(True)

from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.python.filepath import FilePath

import attr
import cattr
import datetime
import appdirs
import json

from attr.validators import instance_of
from math import floor
from typing import List
from random import randint


@attr.s
class Task(object):
    id = attr.ib(validator=instance_of(int))
    name = attr.ib(validator=instance_of(str))
    budget_seconds = attr.ib(validator=instance_of(int))
    budget_per = attr.ib(validator=instance_of(str))
    cutoff = attr.ib(validator=instance_of(str))


@attr.s
class TimeSpent(object):
    started = attr.ib(validator=instance_of(int))
    finished = attr.ib(validator=instance_of(int))


WINDOW_WIDTH = 640
PADDING_WIDTH = 15

task_windows = {}

def seconds_into_clock(total):


    if total < 0:
        prefix = "-"
        total = -total
    else:
        prefix = ""

    return "{}{:02d}:{:02d}:{:02d}".format(prefix, floor(total / 3600), floor((total % 3600) / 60), floor(total % 60))


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
    cutoff_time = datetime.datetime(cd.year, cd.month, cd.day)

    if task.cutoff == "week":
        cutoff_delta = datetime.timedelta(days=datetime.datetime.isoweekday(cutoff_time))

    cutoff_time = (cutoff_time - cutoff_delta).timestamp()

    time_spent_this_per = sum(map(
        lambda s: s.finished - s.started,
        filter(lambda t: t.started > cutoff_time,
               time)))

    return time_spent_this_per


def get_time_needed_for_session(task):

    if task.cutoff == "week":
        if task.budget_per == "day":
            return task.budget_seconds * 7
        elif task.budget_per == "week":
            return task.budget_seconds


def make_task_window(app, myr_task, update_ui):

    time = load_time_spent(myr_task)

    WINDOW_WIDTH = 450

    if myr_task.id in task_windows.keys():
        task_windows[myr_task.id].show()
        return

    box = toga.Box()
    box.style.padding = PADDING_WIDTH

    timer_box = toga.Box()
    timer_box.style.flex_direction = "column"
    timer_box.style.justify_content = "center"

    needed = get_time_needed_for_session(myr_task)
    spent = [get_time_for_session(myr_task, time)]

    started = [0]

    font = toga.Font(DISPLAY_FONT, 90)

    timer_label = toga.Label("00:00", alignment=toga.constants.CENTER_ALIGNED)
    timer_label.style.width = WINDOW_WIDTH - PADDING_WIDTH * 2
    timer_label.style.height = 110
    timer_label.set_font(font)

    session_font = toga.Font(DISPLAY_FONT, 40)

    session_label = toga.Label("00:00:00", alignment=toga.constants.CENTER_ALIGNED)
    session_label.style.width = WINDOW_WIDTH - PADDING_WIDTH * 2
    session_label.style.height = 42
    session_label.set_font(session_font)

    if myr_task.cutoff == "day":
        cutoff_text = "today"
    elif myr_task.cutoff == "week":
        cutoff_text = "this week"

    per_label = toga.Label("remaining " + cutoff_text, alignment=toga.constants.CENTER_ALIGNED)
    per_label.style.width = WINDOW_WIDTH - PADDING_WIDTH * 2

    def update_per_label():
        cd = datetime.date.today()
        cutoff_time = datetime.datetime(cd.year, cd.month, cd.day)

        txt = "remaining " + cutoff_text

        if myr_task.cutoff == "week":
            cutoff_delta = datetime.timedelta(days=datetime.datetime.isoweekday(cutoff_time))

            cutoff_time = (cutoff_time - cutoff_delta + datetime.timedelta(days=6))
            days_remaining = (cutoff_time - datetime.datetime(cd.year, cd.month, cd.day)).days + 1

        if needed - spent[0] > 0:

            if started[0]:
                total = needed - spent[0] + (started[0] - floor(reactor.seconds()))
            else:
                total = needed - spent[0]

            txt += " (" + seconds_into_clock(total / 2) + " per day)"

        per_label.text = txt


    def update_label():
        if started[0]:
            total = needed - spent[0] + (started[0] - floor(reactor.seconds()))
            this_session = floor(reactor.seconds()) - started[0]
        else:
            total = needed - spent[0]
            this_session = 0
        timer_label.text = seconds_into_clock(total)
        session_label.text = seconds_into_clock(this_session)


    update_label()
    update_per_label()

    timer_box.add(session_label)
    timer_box.add(timer_label)
    timer_box.add(per_label)

    button_box = toga.Box()
    button = toga.Button('Start')
    button.style.margin_top = 5

    # lol scopign
    do_things = None
    loops = []

    def stop_things(btn):
        button.label = "Start"
        button.on_press = do_things

        time.append(TimeSpent(
            started=started[0],
            finished=floor(reactor.seconds())))

        started[0] = 0
        spent[0] = get_time_for_session(myr_task, time)
        update_label()
        update_per_label()

        while loops:
            loops.pop().stop()

        save_time_spent(myr_task, time)
        update_ui()

    def dt(btn):
        started[0] = floor(reactor.seconds())
        button.label = "Stop"
        button.on_press = stop_things

        lp = LoopingCall(update_label)
        lp.start(0.1)
        loops.append(lp)
    do_things = dt

    button.on_press = do_things
    button_box.add(button)

    box.add(timer_box)
    box.add(button_box)

    window = toga.Window(title=myr_task.name, position=(150,150),
                         size=(WINDOW_WIDTH,200))

    def on_close():
        stop_things(None)
        task_windows.pop(myr_task.id)

    window.on_close = on_close
    window.content = box
    window.show()

    task_windows[myr_task.id] = window


def make_add_task_window(app, update_ui, update=False):
    """
    Adding tasks...
    """
    WINDOW_WIDTH = 465

    if update is False:
        window_title = "Add New Task"
    else:
        window_title = "Edit " + update.name

    window = toga.Window(size=(WINDOW_WIDTH, 0))

    box = toga.Box()

    box.style.padding = PADDING_WIDTH

    controls_box = toga.Box()
    controls_box.style.flex_direction = 'column'

    name_box = toga.Box()
    name_box.style.flex_direction = 'row'
    name_label = toga.Label("Name:", alignment=toga.constants.RIGHT_ALIGNED)

    name_label.style.padding_top = 3
    name_label.style.width = (WINDOW_WIDTH - PADDING_WIDTH * 2) / 4
    name_label.style.margin_top = 2
    name_label.style.margin_right = 7

    name_entry = toga.TextInput(placeholder='"Practice painting"')
    name_entry.style.width = (WINDOW_WIDTH - PADDING_WIDTH * 2) / 4 * 3


    name_box.add(name_label)
    name_box.add(name_entry)

    per_box = toga.Box()
    per_box.style.margin_top = 7
    per_box.style.flex_direction = 'row'

    per_label = toga.Label("for", alignment=toga.constants.RIGHT_ALIGNED)
    per_label.style.width = (WINDOW_WIDTH - PADDING_WIDTH * 2) / 4
    per_label.style.margin_top = 2
    per_label.style.margin_right = 7

    # Should be number clicky
    per_amount_entry = toga.TextInput(placeholder="20")
    per_amount_entry.style.width = 30

    per_amount_entry_type = toga.TextInput(placeholder="minutes")
    per_amount_entry_type.style.margin_left = 4
    per_amount_entry_type.style.width = 10

    per_amount_for = toga.Label("a")
    per_amount_for.style.margin_right = 4
    per_amount_for.style.margin_left = 7
    per_amount_for.style.margin_top = 2

    # Should be drop down box
    per_duration_entry = toga.TextInput(placeholder="day")

    per_box.add(per_label)
    per_box.add(per_amount_entry)
    per_box.add(per_amount_entry_type)
    per_box.add(per_amount_for)
    per_box.add(per_duration_entry)

    organised_box = toga.Box()
    organised_box.style.margin_top = 7
    organised_box.style.flex_direction = 'row'

    organised_label = toga.Label("Organised by", alignment=toga.constants.RIGHT_ALIGNED)
    organised_label.style.margin_top = 2
    organised_label.style.margin_right = 7
    organised_label.style.width = (WINDOW_WIDTH - PADDING_WIDTH * 2) / 4

    organised_entry = toga.TextInput(placeholder="week")

    organised_box.add(organised_label)
    organised_box.add(organised_entry)

    controls_box.add(name_box)
    controls_box.add(per_box)
    controls_box.add(organised_box)
    box.add(controls_box)

    button_box = toga.Box()
    button_box.style.margin_top = PADDING_WIDTH

    button = toga.Button("Save")

    def get_seconds_per():

        if per_amount_entry_type.value == "seconds":
            seconds_per = float(per_amount_entry.value)
        elif per_amount_entry_type.value == "minutes":
            seconds_per = float(per_amount_entry.value) * 60
        elif per_amount_entry_type.value == "hours":
            seconds_per = float(per_amount_entry.value) * 3600

        return floor(seconds_per)

    def save_new_task(btn):
        tasks = load_tasks()



        tasks.append(Task(id=randint(0, 9999999999999999),
                          name=name_entry.value,
                          budget_seconds=get_seconds_per(),
                          budget_per=per_duration_entry.value,
                          cutoff=organised_entry.value))

        save_tasks(tasks)
        update_ui()
        window.close()


    def update_task(btn):

        tasks = load_tasks()
        tasks.remove(list(filter(lambda x: x.id == update.id, tasks))[0])

        tasks.append(Task(id=update.id,
                          name=name_entry.value,
                          budget_seconds=get_seconds_per(),
                          budget_per=per_duration_entry.value,
                          cutoff=organised_entry.value))

        save_tasks(tasks)
        update_ui()
        window.close()


    if update is False:
        button.on_press = save_new_task
    else:
        name_entry.value = update.name
        per_amount_entry.value = update.budget_seconds
        per_amount_entry_type.value = "seconds"
        per_duration_entry.value = update.budget_per
        organised_entry.value = update.cutoff

        button.on_press = update_task

    button_box.add(button)
    box.add(button_box)

    window.content = box
    window.show()

    pass


def build(app):

    box = toga.Box()
    box.style.padding = PADDING_WIDTH

    itemlist = toga.ScrollContainer(horizontal=False, vertical=True)
    itemlist.style.height = 400
    itemlist.style.width = WINDOW_WIDTH - PADDING_WIDTH * 2
    box.add(itemlist)

    item_label_font = toga.Font("Helvetica", 18)


    def build_itemlist():

        tasks = load_tasks()

        fullbox = toga.Box()
        fullbox.style.width = WINDOW_WIDTH - PADDING_WIDTH * 2

        for task in tasks:
            itembox = toga.Box()
            itembox.style.flex_direction = "row"

            lbl = toga.Label(task.name)
            lbl.style.width = (WINDOW_WIDTH - PADDING_WIDTH * 2) / 4 * 3
            lbl.set_font(item_label_font)

            edit_btn = toga.Button("Edit")
            edit_btn.style.width = (WINDOW_WIDTH - PADDING_WIDTH * 2) / 4 / 2

            btn = toga.Button("Open")
            btn.style.width = (WINDOW_WIDTH - PADDING_WIDTH * 2) / 4 / 2

            lbl.style.height = btn.style.height

            itembox.add(lbl)
            itembox.add(edit_btn)
            itembox.add(btn)
            a = task.id

            def add_buttons(task):
                edit_btn.on_press = lambda _: make_add_task_window(app, build_itemlist, update=task)
                btn.on_press = lambda _: make_task_window(app, task, build_itemlist)

            add_buttons(task)
            fullbox.add(itembox)

        itemlist.content = fullbox
        itemlist._update_layout()

    build_itemlist()

    button_box = toga.Box()
    button = toga.Button('Add New Task')

    def open_new(t):
        window = make_add_task_window(app, build_itemlist)

    button.on_press = open_new
    button_box.add(button)
    box.add(button_box)

    return box


def main():
    app = toga.App('Myriagon', 'net.atleastfornow.myriagon', startup=build)
    app.main_loop()


if __name__ == '__main__':
    main()
