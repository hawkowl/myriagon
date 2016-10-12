import csv
import datetime
import pytz
import time
import toga
import toga.constants

from twisted.python.runtime import platform

from twisted.internet.task import LoopingCall
from twisted.python.filepath import FilePath

from hashlib import sha1
from icalendar import Calendar, Event
from icalendar.prop import vDatetime
from math import floor
from random import randint

from ._tasks import (
    Task,
    load_tasks, save_tasks
)
from ._time import (
    TimeSpent, seconds_into_clock,
    save_time_spent, load_time_spent,
    get_time_for_session, get_time_needed_for_session
)
from ._trash import get_days_in_month

if platform.isMacOSX():
    DISPLAY_FONT = "Helvetica Light"
    FONT_RATIO = 1
    OSX = True
    from twisted.internet.cfreactor import install
    install()
elif platform.isLinux():
    DISPLAY_FONT = "Ubuntu Light"
    FONT_RATIO = 0.8
    OSX = False
    from twisted.internet.gireactor import install
    install(True)


WINDOW_WIDTH = 640
PADDING_WIDTH = 15

task_windows = {}
history_windows = {}


def make_history_window(app, myr_task, update_ui):

    if myr_task.id in history_windows.keys():
        history_windows[myr_task.id].show()
        return

    box = toga.Box()
    box.style.padding = PADDING_WIDTH

    sessions = load_time_spent(myr_task)

    for session in sessions:

        from_entry = toga.TextInput()

        sess_box = toga.Box()

    l = toga.Label("Sorry, nothing here yet.")
    box.add(l)

    window = toga.Window(title="History of " + myr_task.name + " – Myriagon",
                         position=(150, 150), size=(WINDOW_WIDTH, 200),
                         resizeable=False)

    def on_close():
        history_windows.pop(myr_task.id)

    window.on_close = on_close
    window.content = box
    window.show()

    history_windows[myr_task.id] = window


def make_task_window(app, myr_task, update_ui):

    time_spent = load_time_spent(myr_task)

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
    spent = [get_time_for_session(myr_task, time_spent)]

    started = [0]

    font = toga.Font(DISPLAY_FONT, 90 * FONT_RATIO)

    timer_label = toga.Label("00:00", alignment=toga.constants.CENTER_ALIGNED)
    timer_label.style.width = WINDOW_WIDTH - PADDING_WIDTH * 2
    timer_label.style.height = 110
    timer_label.set_font(font)

    session_font = toga.Font(DISPLAY_FONT, 40 * FONT_RATIO)

    session_label = toga.Label("00:00:00",
                               alignment=toga.constants.CENTER_ALIGNED)
    session_label.style.width = WINDOW_WIDTH - PADDING_WIDTH * 2
    session_label.style.height = 42
    session_label.set_font(session_font)

    if myr_task.cutoff == "day":
        cutoff_text = "today"
    elif myr_task.cutoff == "week":
        cutoff_text = "this week"
    elif myr_task.cutoff == "month":
        cutoff_text = "this month"

    per_label = toga.Label("remaining " + cutoff_text,
                           alignment=toga.constants.CENTER_ALIGNED)
    per_label.style.width = WINDOW_WIDTH - PADDING_WIDTH * 2

    def update_per_label():
        cd = datetime.date.today()
        txt = "remaining " + cutoff_text

        if myr_task.cutoff == "week":

            cutoff_time = datetime.datetime(cd.year, cd.month, cd.day)
            cutoff_delta = datetime.timedelta(
                days=datetime.datetime.weekday(cutoff_time))

            cutoff_time = (
                cutoff_time - cutoff_delta + datetime.timedelta(days=7))
            days_remaining = (
                cutoff_time - datetime.datetime(cd.year, cd.month, cd.day)
            ).days
        elif myr_task.cutoff == "month":

            g = get_days_in_month(cd.year, cd.month)
            days_remaining = g - cd.day - 1

        if needed - spent[0] > 0:

            if started[0]:
                total = needed - spent[0] + (started[0] - floor(time.time()))
            else:
                total = needed - spent[0]

            txt += (" (" + seconds_into_clock(total / days_remaining)
                    + " per day)")

        per_label.text = txt

    def update_label():
        if started[0]:
            total = needed - spent[0] + (started[0] - floor(time.time()))
            this_session = floor(time.time()) - started[0]
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
    button_box.style.flex_direction = "row"

    button = toga.Button('Start')
    button.style.margin_top = 5
    button.style.margin_right = 3
    button.style.width = (WINDOW_WIDTH - PADDING_WIDTH * 2) / 2

    secondary_button = toga.Button('Edit History')
    secondary_button.style.margin_top = 5
    secondary_button.style.margin_left = 3
    secondary_button.style.width = (WINDOW_WIDTH - PADDING_WIDTH * 2) / 2

    # lol scopign
    do_things = None
    loops = []

    def cancel():
        print('cancelling')
        started[0] = 0
        spent[0] = get_time_for_session(myr_task, time_spent)

        while loops:
            loops.pop().stop()

        update_label()
        update_per_label()
        update_ui()

    def make_secondary_cancel():
        secondary_button.label = "Cancel"
        secondary_button.on_press = lambda _: cancel()

    def make_secondary_history():
        secondary_button.label = "Edit History"
        secondary_button.on_press = lambda _: make_history_window(
            app, myr_task, update_ui)

    def stop_things(btn):
        make_secondary_history()

        button.label = "Start"
        button.on_press = do_things

        time_spent.append(TimeSpent(
            started=started[0],
            finished=floor(time.time())))

        started[0] = 0
        spent[0] = get_time_for_session(myr_task, time_spent)

        while loops:
            loops.pop().stop()

        save_time_spent(myr_task, time_spent)

        update_label()
        update_per_label()
        update_ui()

    def dt(btn):
        make_secondary_cancel()
        started[0] = floor(time.time())
        button.label = "Stop"
        button.on_press = stop_things

        lp = LoopingCall(update_label)
        lp.start(0.1)
        loops.append(lp)
    do_things = dt

    button.on_press = do_things
    button_box.add(button)
    button_box.add(secondary_button)
    make_secondary_history()

    box.add(timer_box)
    box.add(button_box)

    window = toga.Window(title=myr_task.name + " – Myriagon",
                         position=(150, 150), size=(WINDOW_WIDTH, 200),
                         resizeable=False)

    def on_close():
        if started[0]:
            stop_things(None)
        task_windows.pop(myr_task.id)

    window.on_close = on_close
    window.content = box
    window.show()

    task_windows[myr_task.id] = window


def open_export(window, myr_task):

    filename = window.save_file_dialog(
        "Export " + myr_task.name,
        myr_task.name, ("ics", "csv"))

    if filename is None:
        return

    spent = load_time_spent(myr_task)

    if filename[-3:] == "ics":
        export_to_ical(window, myr_task, spent, filename)
    elif filename[-3:] == "csv":
        export_to_csv(window, myr_task, spent, filename)
    else:
        window.info_dialog("That's not a file format I can understand.",
                           "Sorry, use ics or csv.")
        return

    window.info_dialog(myr_task.name + " saved!",
                       "Your task history was exported to " + filename)


def export_to_csv(window, myr_task, spent, filename):

    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)

        # Header
        csvwriter.writerow([
            "Task Name", "Task Started", "Task Ended", "Length (Seconds)"])

        for session in spent:
            csvwriter.writerow([
                myr_task.name,
                datetime.datetime.utcfromtimestamp(
                    session.started).replace(tzinfo=pytz.utc).isoformat(),
                datetime.datetime.utcfromtimestamp(
                    session.finished).replace(tzinfo=pytz.utc).isoformat(),
                session.finished - session.started])



def export_to_ical(window, myr_task, spent, filename):

    def display(cal):
        print(cal.to_ical().replace(b'\r\n', b'\n').strip().decode('utf8'))

    cal = Calendar()
    cal.add('prodid', '-//atleastfornow.net//myriagon//')
    cal.add('version', '2.0')

    for session in spent:
        e = Event()
        s = sha1((str(session.started) + str(session.finished)).encode('utf8'))

        e['uid'] = s.digest().hex()
        e['summary'] = myr_task.name
        e['dtstart'] = vDatetime(datetime.datetime.utcfromtimestamp(
            session.started).replace(tzinfo=pytz.utc))
        e['dtend'] = vDatetime(datetime.datetime.utcfromtimestamp(
            session.finished).replace(tzinfo=pytz.utc))

        cal.add_component(e)

    with open(filename, 'wb') as f:
        f.write(cal.to_ical())


def make_add_task_window(app, update_ui, update=False):
    """
    Adding tasks...
    """
    WINDOW_WIDTH = 465

    if update is False:
        window_title = "Add New Task"
    else:
        window_title = "Edit " + update.name

    window = toga.Window(size=(WINDOW_WIDTH + PADDING_WIDTH*2, 0), title=window_title,
                         resizeable=False)

    box = toga.Box()
    box.style.padding = PADDING_WIDTH

    if OSX:
        box.style.padding_top = PADDING_WIDTH / 2
        box.style.padding_bottom = PADDING_WIDTH * 2

    controls_box = toga.Box()
    controls_box.style.flex_direction = 'column'

    name_box = toga.Box()
    name_box.style.flex_direction = 'row'
    name_label = toga.Label("Name:", alignment=toga.constants.RIGHT_ALIGNED)

    name_label.style.width = (WINDOW_WIDTH - PADDING_WIDTH * 2) / 4
    name_label.style.margin_top = 3
    name_label.style.margin_right = 7

    name_entry = toga.TextInput(placeholder='"Practice painting"')
    name_entry.style.width = ((WINDOW_WIDTH - PADDING_WIDTH * 2) / 4) * 3

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
    per_amount_entry = toga.NumberInput(max_value=99999)

    per_amount_entry_type = toga.Selection(
        items=("seconds", "minutes", "hours"))
    per_amount_entry_type.style.margin_left = 4

    per_amount_for = toga.Label("a")
    per_amount_for.style.margin_right = 4
    per_amount_for.style.margin_left = 7
    per_amount_for.style.margin_top = 2

    per_duration_entry = toga.Selection(items=("day", "week", "month"))

    per_box.add(per_label)
    per_box.add(per_amount_entry)
    per_box.add(per_amount_entry_type)
    per_box.add(per_amount_for)
    per_box.add(per_duration_entry)

    organised_box = toga.Box()
    organised_box.style.margin_top = 2
    organised_box.style.flex_direction = 'row'

    organised_label = toga.Label("Organised by",
                                 alignment=toga.constants.RIGHT_ALIGNED)
    organised_label.style.margin_top = 2
    organised_label.style.margin_right = 7
    organised_label.style.width = (WINDOW_WIDTH - PADDING_WIDTH * 2) / 4

    organised_entry = toga.Selection(items=("week", "month", "year"))

    organised_box.add(organised_label)
    organised_box.add(organised_entry)

    controls_box.add(name_box)
    controls_box.add(per_box)
    controls_box.add(organised_box)
    controls_box.rehint()

    box.add(controls_box)

    button_box = toga.Box()
    button_box.style.margin_top = 2

    button = toga.Button("Save")
    button_box.add(button)

    if not OSX:
        button_box.style.margin_top = 7

    box.add(button_box)
    box.rehint()

    def get_seconds_per():

        if per_amount_entry_type.value == "seconds":
            seconds_per = float(per_amount_entry.value)
        elif per_amount_entry_type.value == "minutes":
            seconds_per = float(per_amount_entry.value) * 60
        elif per_amount_entry_type.value == "hours":
            seconds_per = float(per_amount_entry.value) * 3600

        return floor(seconds_per)

    def save_new_task(btn):
        try:
            float(per_amount_entry.value)
        except:
            window.info_dialog(
                "You didn't enter a number!",
                "Please set the number of " + per_amount_entry_type.value)
            return

        tasks = load_tasks()

        tasks.append(Task(id=randint(0, 9999999999999999),
                          name=name_entry.value,
                          budget_seconds=get_seconds_per(),
                          budget_per=per_duration_entry.value,
                          cutoff=organised_entry.value,
                          since=floor(time.time())))

        save_tasks(tasks)
        update_ui()
        window.close()

    def update_task(btn):
        try:
            float(per_amount_entry.value)
        except Exception as e:
            print(e)
            window.info_dialog(
                "You didn't enter a number!",
                "Please set the number of " + per_amount_entry_type.value)
            return

        tasks = load_tasks()
        tasks.remove(list(filter(lambda x: x.id == update.id, tasks))[0])

        tasks.append(Task(id=update.id,
                          name=name_entry.value,
                          budget_seconds=get_seconds_per(),
                          budget_per=per_duration_entry.value,
                          cutoff=organised_entry.value,
                          since=update.since))

        save_tasks(tasks)
        update_ui()
        window.close()

    if update is False:
        button.on_press = save_new_task
    else:
        name_entry.value = update.name

        if update.budget_seconds > 3599:
            per_amount_entry.value = update.budget_seconds / 3600
            per_amount_entry_type.value = "hours"
        elif update.budget_seconds > 59:
            per_amount_entry.value = update.budget_seconds / 60
            per_amount_entry_type.value = "minutes"
        else:
            per_amount_entry.value = update.budget_seconds
            per_amount_entry_type.value = "seconds"

        per_duration_entry.value = update.budget_per
        organised_entry.value = update.cutoff

        button.on_press = update_task

    window.content = box
    window.show()


def build(app):

    box = toga.Box()
    box.style.padding = PADDING_WIDTH

    itemlist = toga.ScrollContainer(horizontal=False, vertical=True)
    itemlist.style.height = 450
    itemlist.style.width = WINDOW_WIDTH - PADDING_WIDTH * 2
    box.add(itemlist)

    item_label_font = toga.Font("Helvetica", 18 * FONT_RATIO)

    def build_itemlist():

        tasks = load_tasks()

        fullbox = toga.Box()
        fullbox.style.width = WINDOW_WIDTH - PADDING_WIDTH * 2

        for task in tasks:
            itembox = toga.Box()
            itembox.style.flex_direction = "row"

            lbl = toga.Label(task.name)
            lbl.style.width = (WINDOW_WIDTH - PADDING_WIDTH * 2) / 4 * 2
            lbl.set_font(item_label_font)

            export_btn = toga.Button("Export")
            export_btn.style.width = (WINDOW_WIDTH - PADDING_WIDTH * 2) / 2 / 3

            edit_btn = toga.Button("Edit")
            edit_btn.style.width = (WINDOW_WIDTH - PADDING_WIDTH * 2) / 2 / 3

            btn = toga.Button("Open")
            btn.style.width = (WINDOW_WIDTH - PADDING_WIDTH * 2) / 2 / 3

            lbl.style.height = btn.style.height

            itembox.add(lbl)
            itembox.add(export_btn)
            itembox.add(edit_btn)
            itembox.add(btn)

            def add_buttons(task):
                export_btn.on_press = lambda _: open_export(
                    app.main_window, task)
                edit_btn.on_press = lambda _: make_add_task_window(
                    app, build_itemlist, update=task)
                btn.on_press = lambda _: make_task_window(
                    app, task, build_itemlist)

            add_buttons(task)
            fullbox.add(itembox)

        itemlist.content = fullbox
        itemlist._update_layout()

    build_itemlist()

    button_box = toga.Box()

    button = toga.Button('Add New Task')

    def open_new(t):
        make_add_task_window(app, build_itemlist)

    button.on_press = open_new
    button_box.add(button)
    box.add(button_box)

    app.main_window.title = "Myriagon"

    return box


def main():
    app = toga.App(
        'Myriagon', 'net.atleastfornow.myriagon', startup=build,
        icon=FilePath(__file__).parent().child("myriagon.icns").path)
    app.main_loop()


if __name__ == '__main__':
    main()
