"""
Convert an iCAL to an HTML page for later convenient packing

This generates three html documents, in the timezones declared in "tzs"
from the ical accessible at "url"
"""
import argparse
import html
import os
import subprocess
import time
import urllib.error
import urllib.request
from datetime import timedelta
from string import Template

import cv2
from dateutil import tz

from ics import *
from gdrive_upload import batch_upload, setup_service, download_banner

from sys import platform

LINUX_MODE = True
FFMPEG_PATH = 'ffmpeg'  # if it's already on your path, you don't need to use the absolute path
FIREFOX_PATH = 'xvfb-run firefox'

if platform == "win32":
    LINUX_MODE = False
    FIREFOX_PATH = '"c:\\Program Files\\Mozilla Firefox\\firefox.exe"'

LOOKAHEAD = 14  # Days
ENABLE_DESCRIPTIONS = False
MAX_DETAIL_LINES = 4
CHARS_PER_DETAIL_LINE = 80

BANNER_ID = "19P7CCDuquFFzNnOz4-nu4ZtgkFAHUepj"
BANNER_PATH = "html-resources/banner/current.png"


def filesafe_str(in_str):
    return "".join([c for c in in_str if c.isalpha() or c.isdigit() or c == ' ' or c == '-' or c == '+']).rstrip()


def generate_calendars(ical_url, canonical_tzs, use_cache=False):
    if use_cache and os.path.exists("calendar.ical"):
        # print("Using Cached")
        with open("calendar.ical", "r", encoding="utf-8") as f:
            ics_string = f.read()
    else:
        # print("Requesting Calendar")
        with urllib.request.urlopen(ical_url) as response:
            try:
                ics_string = response.read()
            except urllib.error as e:
                print(e)
                raise

        if use_cache:
            with open('calendar.ical', "wb") as f:
                f.write(ics_string)

    with open("html-resources/template/head.html", "r", encoding="utf-8") as f:
        head_html_template = Template(f.read())
    with open("html-resources/template/tail.html", "r", encoding="utf-8") as f:
        tail_html = f.read()

    files = []
    for can_tz in canonical_tzs:
        loc_tz = tz.gettz(can_tz)
        today = datetime.now(loc_tz)
        # For generating files with the UTC offset in the filename instead, use this:
        offset = today.utcoffset() - today.astimezone(timezone.utc).utcoffset()
        offset_num = int(offset.total_seconds() / 3600)
        offset_h = str(offset_num)
        if offset_num >= 0:
            offset_h = '+' + offset_h
        # if you instead wish to use the canonical name, pass in "loc_tz" instead of "offset_h" here:
        filename = f'cal_{filesafe_str(str(offset_h))}.html'
        window_end = today + timedelta(days=LOOKAHEAD)
        events = get_events_from_ics(ics_string, today, window_end, loc_tz)
        fname = os.path.abspath("output/html") + os.sep + filename
        files.append(fname)
        with open(fname, "w", encoding="utf-8") as out:
            out.write(head_html_template.substitute(timezone=str(offset_h)))
            out.write(f"<div class=\"calendar\"><table>\n")
            day = None
            for e in events:
                evt_start = e['startdt'].astimezone(tz=loc_tz)
                e_date = evt_start.strftime('%b %d')
                if e_date != day:
                    out.write(f"\t<tr><td colspan=\"2\" class=\"date\">{e_date}</td></tr>\n")
                day = e_date
                evt_end = e.get('enddt', None)

                if e['allday']:
                    time_line = f"\t<tr><td class=\"starttime\">&nbsp;</td>"
                elif evt_end:
                    evt_end = evt_end.astimezone(tz=loc_tz)
                    time_line = f"\t<tr><td class=\"starttime\">{evt_start.strftime('%H:%M')} ~ " + \
                                f"<span class=\"endtime\">{evt_end.strftime('%H:%M')}</span></td>"
                else:
                    time_line = f"\t<tr><td class=\"starttime\">{evt_start.strftime('%H:%M')}</td>"

                summary_line = f"<td class=\"summary{' allday' if e['allday'] else ''}\">{html.escape(e['summary'])}"

                desc_line = ""
                if ENABLE_DESCRIPTIONS and e['desc'] and len(e['desc']) > 4:
                    desc_array = list(filter(None, e['desc'].split('\n')))
                    trunc = False
                    if len(desc_array) > MAX_DETAIL_LINES:
                        desc_array = desc_array[:MAX_DETAIL_LINES]
                        trunc = True
                    desc_str = '\n'.join(desc_array)
                    if len(desc_str) > (CHARS_PER_DETAIL_LINE * MAX_DETAIL_LINES):
                        desc_str = desc_str[:CHARS_PER_DETAIL_LINE * MAX_DETAIL_LINES]
                        desc_str = desc_str[:desc_str.rfind(" ")]
                        trunc = True
                    if trunc:
                        desc_str = desc_str + "...\n[Description Truncated; More info on online calendar]"

                    desc_line = f"<br /><span class=\"details\">{html.escape(desc_str)}</span>"

                details_close = "</td></tr>\n"

                out.write(time_line + summary_line + desc_line + details_close)

            out.write("</table>\n</div>\n")
            out.write(tail_html)
        print("*", end="", flush=True)
    return files


def generate_with_firefox(html_paths):
    calendar_images_tmp = []
    suppress_opt = ''
    if LINUX_MODE:
        suppress_opt = ' >/dev/null 2>&1'
    for in_path in html_paths:
        out_path = in_path.replace(".html", ".png").replace("html", "screenshot-in")
        calendar_images_tmp.append(out_path)
        subprocess.run(
            FIREFOX_PATH +
            ' --headless --profile TEMP_FIREFOX --no-remote' +
            f' --screenshot {out_path}' +
            f' file:///{in_path} ' +
            ' --window-size=2048,8192' + suppress_opt, shell=LINUX_MODE)
        os.remove(in_path)
        print("*", end="", flush=True)

    return calendar_images_tmp


def reshape_with_ocv(image_paths):
    result_paths = []
    for full_path in image_paths:
        image = cv2.imread(full_path)
        try:
            if image.size == 0:
                print(f"Image did not exist at path {full_path}")
                continue
        except AttributeError:
            print(f"Image did not exist at path {full_path}")
            continue
        sz = image.shape  # y, x, z
        im_l = image[:sz[1] * 2, :, :]
        im_r = image[sz[1] * 2:, :, :]
        im_h = cv2.hconcat([im_l, im_r])
        new_path = full_path.replace("screenshot-in", "screenshot-out")
        result_paths.append(new_path)
        cv2.imwrite(new_path, im_h)
        os.remove(full_path)
        print("*", end="", flush=True)
    return result_paths


def embed_into_mp4(image_paths):
    result_paths = []
    for full_path in image_paths:
        new_path = full_path.replace(".png", ".mp4")
        new_path = new_path.replace("screenshot-out", "mp4")
        result_paths.append(new_path)
        subprocess.run(
            FFMPEG_PATH +
            ' -y -hide_banner -loglevel error' +
            f' -i {full_path}' +
            ' -c:v libx264 -pix_fmt yuv420p' +
            f' {new_path}', shell=LINUX_MODE)
        os.remove(full_path)
        print("*", end="", flush=True)
    return result_paths


def print_elapsed(last_t):
    segment = time.time()
    print(f'] {segment - last_t :.2f}s', flush=True)
    return segment


def do_tasks(args, goog_service):
    url = 'https://calendar.google.com/calendar/ical/' + \
          'a62rkiqhau8bn341cepfbc4k0s%40group.calendar.google.com/public/basic.ics'

    tzs = []
    for i in range(12 + 14 + 1):
        tz_num_etc = i - 14
        if tz_num_etc >= 0:
            tz_num_etc = '+' + str(tz_num_etc)
        can_string = f"Etc/GMT{tz_num_etc}"
        tzs.append(can_string)

    if args.url is not None:
        url = args.url
    if args.tzs is not None:
        if isinstance(args.tzs, list):
            tzs = args.tzs
        else:
            tzs = [args.tzs]

    start = time.time()
    last = start
    total = len(tzs)
    print(f"Generating Calendars for {total} timezones\n[", end="")
    cal_results = generate_calendars(url, tzs, args.cache)
    last = print_elapsed(last)

    print(f"Rendering images from html\n[", end="")
    pre_imgs = generate_with_firefox(cal_results)
    last = print_elapsed(last)

    print(f"Formatting to Square with OpenCV\n[", end="")
    post_imgs = reshape_with_ocv(pre_imgs)
    last = print_elapsed(last)

    print(f"Using FFMPEG to embed in an MP4\n[", end="")
    post_mp4 = embed_into_mp4(post_imgs)
    last = print_elapsed(last)

    if goog_service:
        print(f"Uploading files to Google Drive\n[", end="")
        batch_upload(goog_service, post_mp4)
        print_elapsed(last)

    end = time.time()
    print(f"Completed in {end - start :.2f}s")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate some calendars')
    parser.add_argument("-url", default=None, help="url to the .ical")
    parser.add_argument("-tzs", default=None, metavar='T', nargs='+', help="list of canonical timezones")
    parser.add_argument("-cache", action='store_true', default=False, help="Enable locally caching ical")
    args = parser.parse_args()

    # If gdrive_service is none, this will still return run but skip all google steps.
    gdrive_service = setup_service()
    success = download_banner(gdrive_service, BANNER_ID, BANNER_PATH)
    if success:
        do_tasks(args, gdrive_service)
