import datetime

def ft_ct(filetime):
    hl = filetime.split()
    timestamp = int(hl[0])
    timestamp <<= 32
    timestamp |= int(hl[1])
    return (datetime.datetime(1601, 1, 1, 0, 0, 0) +\
            datetime.timedelta(microseconds=timestamp/10)).ctime()

def time_diff(earlier, later):
    total_time = later - earlier
    total_seconds = int(total_time)
    
    days    = int(total_seconds / 86400)
    hours   = int(total_seconds % 86400 / 3600)
    minutes = int(total_seconds % 3600 / 60)
    seconds = int(total_seconds % 60)
    if total_seconds < 60:
        milliseconds = int((total_time - total_seconds) * 1000)
    else:
        milliseconds = 0

    string = ''
    if days > 0:
        string += str(days) + ' da' + (days == 1 and 'y' or 'ys') + ', '
    if len(string) > 0 or hours > 0:
        string += str(hours) + ' hou' + (hours == 1 and 'r' or 'rs') + ', '
    if len(string) > 0 or minutes > 0:
        string += str(minutes) + ' minut' + (minutes == 1 and 'e' or 'es') + ', '
    if len(string) > 0 or seconds > 0:
        string += str(seconds) + ' secon' + (seconds == 1 and 'd' or 'ds')
        if milliseconds > 0:
            string += ', '
    if milliseconds > 0:
        string += str(milliseconds) + ' millisecon' +\
                  (milliseconds == 1 and 'd' or 'ds')

    return string
