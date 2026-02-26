import datetime


def get_first_matching_date(start_date_str, days):
    day_map = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}
    start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
    weekdays = [day_map[code] for code in days]

    for i in range(7):
        candidate = start_date + datetime.timedelta(days=i)
        if candidate.weekday() in weekdays:
            return str(candidate)
    return None
