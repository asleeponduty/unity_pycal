# .ical -> Unity-compatible calendar project
The goal of this project is to take a publicly-accessible internet calendar in ical format, parse upcoming two weeks, 
and generate an aesthetically-pleasing image for use inside any game that has a built-in video player and support for custom shaders. 

For our needs, we generate 27 calendars from the input. This is to cover every UTC offset. 
Typically, game engines such as Unity provide a means for determining the local UTC offset. 
This enables the user to see their local calendar, without the overhead of a mental conversion while immersed in a game.

## Rationale
This project was inspired by Unity's inability to display a webpage in game (without heavy overhead), and the desire to have a weekly event calendar viewable in game.

Based on previous findings, the simplest way to get an image media in game is to use the default video player to load a single-frame video. 
MP4 compression has been shown to take a single uncompressed 4k png image weighing in at 2,211kb and compressing it down to 232kb. This same image compressed with pngquant only gets down to 541kb. 
While the compressed png is excellent, utilizing the basic unity video player allows cross-platform access without providing a custom script to perform a web request and fetch an image. 

## What this does
1. Consume an existing web-accessible .ical, convert it into representative timezones, 
and generate HTML in a pleasing format
2. Use Firefox in headless mode to generate 2048x8192px images of the calendar in each of the 27 UTC offsets (-12 thru +14)
3. Manipulate the images using python-opencv to construct the calendar 4k square image, compliant with the scroll shader used in Unity. 
4. Encode each image into a single-frame mp4 
5. upload to google drive using an OAUTH2.0 Token

## Steps in Unity

<ol start="6">
<li>Configure the unity project to discriminate between the user's locales</li>
<li>Use the users' locale to select the correct asset url from Google Drive</li>
<li>Feed the correct url to the <a href="https://github.com/AoiKamishiro/VRC_UdonEventCalendar">Calendar Prefab</a></li>
</ol>


## References you need for this project:
* Python3+
* FFMPEG
* Noto Sans fonts (below)
* (optional) an authorized application with Google OAUTH 2.0 with scopes for writing to google drive
* firefox
* (Linux) xvfb, for running on systems without displays

### Python Libraries (pip):
* python-dateutil
* icalendar
* opencv-python
* urllib3
* google-api-python-client 
* google-auth-httplib2 
* google-auth-oauthlib

### Fonts
Google's ["Noto Sans JP"]("https://fonts.google.com/specimen/Noto+Sans+JP") font needs to be extracted to the fonts/Noto_Sans_JP directory


### Google OAUTH
Follow Google's [quickstart tutorial]("https://developers.google.com/drive/api/v3/quickstart/python") and download your 
OAUTH credentials to `gdrive/client_secret.json`

Create a publicly visible google drive folder, and upload your current banner and all 27 generated calendar mp4 files to it.
Record the ids of these mp4 files in `gdrive/upload_file_dict.py`, and the id of your banner in `main.py`

If you're unable to make credentials at this time, this program will still run. 
However, it will neither be able to retrieve the latest banner picture nor upload to the publicly-shared folder.  

An authorized application will "update" the existing uploads in the google drive folder, retaining the original download url.