from ics import *
import urllib.request
from datetime import datetime, timedelta
import os
import tzlocal


def filesafe_str(in_str):
    return "".join([c for c in in_str if c.isalpha() or c.isdigit() or c == ' ']).rstrip()


url = 'https://calendar.google.com/calendar/ical/' + \
      'a62rkiqhau8bn341cepfbc4k0s%40group.calendar.google.com/public/basic.ics'
ics_string = ""

fonts_s = '<link rel="preconnect" href="https://fonts.gstatic.com">' + \
          '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP&display=swap" rel="stylesheet"> '
style_s = '<link rel=\"stylesheet\" href=\"dummy.css\"/>'
head = "<!DOCTYPE html>\n<html>\n<head>" + style_s + "</head><body>\n"

tail = "</body></html>"
if not os.path.exists("calendar.ical"):
    print("Requesting Calendar from Google")
    with urllib.request.urlopen(url) as response:
        ics_string = response.read()
    with open('calendar.ical', "wb") as f:
        f.write(ics_string)
else:
    print("Using Cached")
    with open("calendar.ical", "r") as f:
        ics_string = f.read()

tzs = [timezone.utc, tzlocal.get_localzone()]
for tz in tzs:
    print(f"Using TZ {tz}")
    window_start = datetime.now(tz)
    window_end = window_start + timedelta(days=7)
    events = get_events_from_ics(ics_string, window_start, window_end, tz)
    with open(f"cal_{filesafe_str(str(tz))}.html", "w") as out:
        out.write(head)
        out.write(f"<div class=\"calendar\"><table>\n")
        day = None
        for e in events:
            start = e['startdt'].astimezone(tz=tz)
            e_date = start.strftime('%b %d')
            if e_date != day:
                # if day is not None:
                #     out.write("</table>\n")
                #out.write(f"\t<tr><th></th><th></th></th>\n")
                out.write(f"\t<tr><td colspan=\"2\" class=\"date\">{e_date}</td></tr>\n")
                print(e_date)
            day = e_date
            # mt = False
            # if localzone == timezone.utc:
            #     mt = True
            if e['allday']:
                print(f"{e['summary']} - All Day")
                #
                out.write(f"\t<tr><td class=\"starttime\">&nbsp;</td>" +
                          f"<td class=\"allday summary\">{e['summary']}</td></tr>\n")
            else:
                print(f"{start.strftime('%H:%M')} - {e['summary']}")
                end = e.get('enddt', None)
                if end:
                    end = end.astimezone(tz=tz)
                    out.write(f"\t<tr><td class=\"starttime\">{start.strftime('%H:%M')} ~ " +
                              f"<span class=\"endtime\">{end.strftime('%H:%M')}</span></td>" +
                              f"<td class=\"summary\">{e['summary']}</td></tr>\n")
                else:
                    out.write(f"\t<tr><td class=\"starttime\">{start.strftime('%H:%M')}</td>" +
                              f"<td class=\"summary\">{e['summary']}</td></tr>\n")
                # if mt:
                #     print(f"{local_time.strftime('%H:%M')} - {e['summary']}")
                # else:
                #     print(f"{local_time.strftime('%I:%M %p')} - {e['summary']}")
        out.write("</table>\n</div>\n")
        out.write(tail)
    print("* " * 10)
