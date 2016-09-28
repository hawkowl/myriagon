import toga
import toga.constants

from twisted.internet.cfreactor import install
install()

from twisted.internet import reactor, task
import attr
import datetime
from math import floor


@attr.s
class Task(object):
    id = attr.ib()
    name = attr.ib()
    budget = attr.ib()
    cutoff = attr.ib()

@attr.s
class TimeSpent(object):
    started = attr.ib()
    finished = attr.ib()


WINDOW_WIDTH = 640
PADDING_WIDTH = 10

task_windows = {}


time_spent = {
    1: []
}



tasks = [

    Task(id=1, name="Thing", budget=(60, "day"), cutoff="week"),

]


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

    seconds, per = task.budget

    if task.cutoff == "week":
        if per == "day":
            return seconds * 7





def make_task_window(app, myr_task):

    if myr_task.id in task_windows.keys():
        task_windows[myr_task.id].show()
        return

    box = toga.Box()
    box.style.padding = 10

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


def build(app):

    box = toga.Box()
    box.style.padding = 10

    fullbox = toga.Box()
    fullbox.style.width = WINDOW_WIDTH - PADDING_WIDTH * 2

    itemlist = toga.ScrollContainer(horizontal=False, vertical=True)
    itemlist.style.height = 400
    itemlist.style.width = WINDOW_WIDTH - PADDING_WIDTH * 2
    box.add(itemlist)

    for task in tasks:
        itembox = toga.Box()
        itembox.style.flex_direction = "row"

        lbl = toga.Label(task.name)
        lbl.style.width = (WINDOW_WIDTH - PADDING_WIDTH * 2) / 4 * 3


        btn = toga.Button("Open")
        btn.style.width = (WINDOW_WIDTH - PADDING_WIDTH * 2) / 4


        itembox.add(lbl)
        itembox.add(btn)
        btn.on_press = lambda _: make_task_window(app, task)
        fullbox.add(itembox)

    button_box = toga.Box()
    button = toga.Button('Go go go')

    def open_new(t):
        window = make_task_window()
        window.show()

    button.on_press = open_new
    button_box.add(button)

    app.main_window.size = (100,100)

    itemlist.content = fullbox
    box.add(button_box)

    return box


if __name__ == '__main__':
    app = toga.App('Myriagon', 'net.atleastfornow.myriagon', startup=build)
    app.main_loop()
