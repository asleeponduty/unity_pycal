"""
Convert an iCAL to an HTML page for later convenient packing

This generates three html documents, in the timezones declared in "tzs"
from the ical accessible at "url"
"""
import argparse
from datetime import timedelta
from dateutil import tz
import html
from ics import *
import os
from string import Template
import urllib.request
import subprocess

import cv2

LOOKAHEAD = 14  # Days


def filesafe_str(in_str):
    return "".join([c for c in in_str if c.isalpha() or c.isdigit() or c == ' ']).rstrip()


def generate_calendars(ical_url, canonical_tzs, use_cache=False):
    head = "<!DOCTYPE html>\n<html>\n<head>" + \
           '<meta charset="UTF-8">' + \
           '<link rel=\"stylesheet\" href=\"style.css\"/>' + "</head><body>\n"
    tail = "</div>\n</body></html>"

    body_pre = Template(
        '<div class="top">\n'
        '\t<div class="scrollbar"></div>\n' +
        '\t<div class="header"><img src="banner/current.png"></div>\n' +
        '\t<div class="spacer"></div>\n' +
        '\t<div class="footer">Poonis Technologies - $timezone</div>\n' +
        '</div>\n'
        '<div class="bottom">\n' +
        '\t<div class="scrollbar"></div>\n')

    if use_cache and os.path.exists("calendar.ical"):
        # print("Using Cached")
        with open("calendar.ical", "r") as f:
            ics_string = f.read()
    else:
        # print("Requesting Calendar")
        with urllib.request.urlopen(ical_url) as response:
            ics_string = response.read()
        if use_cache:
            with open('calendar.ical', "wb") as f:
                f.write(ics_string)

    files = []

    for can_tz in canonical_tzs:
        loc_tz = tz.gettz(can_tz)
        window_start = datetime.now(loc_tz)
        # For generating files with the UTC offset in the filename instead, use this:
        # offset = loc_tz.utcoffset(window_start)
        # offset_h = str(offset.seconds / 3600)
        window_end = window_start + timedelta(days=LOOKAHEAD)
        events = get_events_from_ics(ics_string, window_start, window_end, loc_tz)
        fname = f"cal_{filesafe_str(str(loc_tz))}.html"
        files.append((fname, can_tz))
        with open(fname, "w", encoding="utf-8") as out:
            out.write(head)
            out.write(body_pre.substitute(timezone=can_tz))
            out.write(f"<div class=\"calendar\"><table>\n")
            day = None
            for e in events:
                start = e['startdt'].astimezone(tz=loc_tz)
                e_date = start.strftime('%b %d')
                if e_date != day:
                    out.write(f"\t<tr><td colspan=\"2\" class=\"date\">{e_date}</td></tr>\n")
                day = e_date
                if e['allday']:
                    out.write(f"\t<tr><td class=\"starttime\">&nbsp;</td>" +
                              f"<td class=\"allday summary\">{html.escape(e['summary'])}</td></tr>\n")
                else:
                    end = e.get('enddt', None)
                    if end:
                        end = end.astimezone(tz=loc_tz)
                        out.write(f"\t<tr><td class=\"starttime\">{start.strftime('%H:%M')} ~ " +
                                  f"<span class=\"endtime\">{end.strftime('%H:%M')}</span></td>" +
                                  f"<td class=\"summary\">{html.escape(e['summary'])}</td></tr>\n")
                    else:
                        out.write(f"\t<tr><td class=\"starttime\">{start.strftime('%H:%M')}</td>" +
                                  f"<td class=\"summary\">{html.escape(e['summary'])}</td></tr>\n")
            out.write("</table>\n</div>\n")
            out.write(tail)
        print("*", end="")
    return files


def generate_with_firefox(result_tuples):
    calendar_images_tmp = []
    for filename, can_tz in result_tuples:
        cal_fname = f'calendar_{filesafe_str(can_tz)}.png'
        cal_path = os.path.abspath("output/tmp") + os.sep + cal_fname
        calendar_images_tmp.append(cal_path)
        subprocess.run(
            'c:\\Program Files\\Mozilla Firefox\\firefox.exe' +
            ' --headless --profile TEMP_FIREFOX --no-remote' +
            f' --screenshot {cal_path}' +
            f' file:///{os.path.abspath(filename)} ' +
            ' --window-size=512,2048')
        print("*", end="")

    return calendar_images_tmp


def reshape_with_ocv(image_paths):
    for full_path in image_paths:
        image = cv2.imread(full_path)
        sz = image.shape  # y, x, z
        im_l = image[:sz[1]*2, :, :]
        im_r = image[sz[1]*2:, :, :]
        im_h = cv2.hconcat([im_l, im_r])
        new_path = full_path.replace(os.sep + "tmp", "")
        cv2.imwrite(new_path, im_h)
        os.remove(full_path)
        print("*", end="")


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

    total = len(tzs)
    print(f"Generating Calendars for {total} timezones")
    cal_results = generate_calendars(url, tzs, args.cache)
    print(']')
    print(f"Rendering images from html\n[", end="")
    pre_imgs = generate_with_firefox(cal_results)
    print(']')
    print(f"Formatting to Square with OpenCV\n[", end="")
    reshape_with_ocv(pre_imgs)
    print(']')
