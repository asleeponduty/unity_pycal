"""
Convert an iCAL to an HTML page for later convenient packing

This generates three html documents, in the timezones declared in "tzs"
from the ical accessible at "url"
"""
import argparse
from dateutil import tz
import html
from ics import *
import os
import urllib.request


def filesafe_str(in_str):
    return "".join([c for c in in_str if c.isalpha() or c.isdigit() or c == ' ']).rstrip()


def generate_calendars(ical_url, canonical_tzs, use_cache=False):
    head = "<!DOCTYPE html>\n<html>\n<head>" + \
           '<meta charset="UTF-8">' + \
           '<link rel=\"stylesheet\" href=\"style.css\"/>' + "</head><body>\n"
    tail = "</body></html>"

    if use_cache and os.path.exists("calendar.ical"):
        print("Using Cached")
        with open("calendar.ical", "r") as f:
            ics_string = f.read()
    else:
        print("Requesting Calendar")
        with urllib.request.urlopen(ical_url) as response:
            ics_string = response.read()
        if use_cache:
            with open('calendar.ical', "wb") as f:
                f.write(ics_string)
    tz_list = []
    for can_tz in canonical_tzs:
        tz_list.append(tz.gettz(can_tz))

    for loc_tz in tz_list:
        print(f"Using TZ {loc_tz}")
        window_start = datetime.now(loc_tz)
        # For generating files with the UTC offset instead, use this:
        # offset = loc_tz.utcoffset(window_start)
        # offset_h = str(offset.seconds / 3600)
        window_end = window_start + timedelta(days=7)
        events = get_events_from_ics(ics_string, window_start, window_end, loc_tz)
        with open(f"cal_{filesafe_str(str(loc_tz))}.html", "w", encoding="utf-8") as out:
            out.write(head)
            out.write(f"<div class=\"calendar\"><table>\n")
            day = None
            for e in events:
                start = e['startdt'].astimezone(tz=loc_tz)
                e_date = start.strftime('%b %d')
                if e_date != day:
                    # if day is not None:
                    #     out.write("</table>\n")
                    # out.write(f"\t<tr><th></th><th></th></th>\n")
                    out.write(f"\t<tr><td colspan=\"2\" class=\"date\">{e_date}</td></tr>\n")
                    print(e_date)
                day = e_date
                # mt = False
                # if localzone == timezone.utc:
                #     mt = True
                if e['allday']:
                    print(f"{html.escape(e['summary'])} - All Day")
                    #
                    out.write(f"\t<tr><td class=\"starttime\">&nbsp;</td>" +
                              f"<td class=\"allday summary\">{html.escape(e['summary'])}</td></tr>\n")
                else:
                    print(f"{start.strftime('%H:%M')} - {html.escape(e['summary'])}")
                    end = e.get('enddt', None)
                    if end:
                        end = end.astimezone(tz=loc_tz)
                        out.write(f"\t<tr><td class=\"starttime\">{start.strftime('%H:%M')} ~ " +
                                  f"<span class=\"endtime\">{end.strftime('%H:%M')}</span></td>" +
                                  f"<td class=\"summary\">{html.escape(e['summary'])}</td></tr>\n")
                    else:
                        out.write(f"\t<tr><td class=\"starttime\">{start.strftime('%H:%M')}</td>" +
                                  f"<td class=\"summary\">{html.escape(e['summary'])}</td></tr>\n")
                    # if mt:
                    #     print(f"{local_time.strftime('%H:%M')} - {e['summary']}")
                    # else:
                    #     print(f"{local_time.strftime('%I:%M %p')} - {e['summary']}")
            out.write("</table>\n</div>\n")
            out.write(tail)
        print("* " * 10)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate some calendars')
    parser.add_argument("-url", default=None, help="url to the .ical")
    parser.add_argument("-tzs", default=None, metavar='T', nargs='+', help="list of canonical timezones")
    parser.add_argument("-cache", action='store_true', default=False, help="Enable locally caching ical")
    args = parser.parse_args()

    url = 'https://calendar.google.com/calendar/ical/' + \
          'a62rkiqhau8bn341cepfbc4k0s%40group.calendar.google.com/public/basic.ics'

    tzs = ['America/Los_Angeles', 'America/New_York', 'Etc/UTC', 'Europe/London',
           'Europe/Berlin', 'Asia/Singapore', 'Pacific/Auckland']

    if args.url is not None:
        url = args.url
    if args.tzs is not None:
        if isinstance(args.tzs, list):
            tzs = args.tzs
        else:
            tzs = [args.tzs]

    generate_calendars(url, tzs, args.cache)
