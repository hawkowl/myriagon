def get_days_in_month(year, month):

    # 30 days has september, april, june, and november
    # all the rest have 31, except for feb
    # special snowflake, isn't it

    is_leap_year = year % 4 == 0

    days = {
        1: 31,
        2: 29 if is_leap_year else 28,
        3: 31,
        4: 30,
        5: 31,
        6: 30,
        7: 31,
        8: 31,
        9: 31,
        10: 31,
        11: 30,
        12: 31,
    }

    return days[month]
