import datetime

def format_timestamp(ts):
    dt = datetime.datetime.fromtimestamp(ts)
    dt_label = '{:04}/{:02}/{:02} {:02}:{:02}:{:02}'.format(
        dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    return dt_label

def timestamp_lst_to_date_lst(ts_lst):
    dt_lst = []
    for ts in ts_lst:
        dt = format_timestamp(ts)
        dt_lst.append(dt)
    return dt_lst