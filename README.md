# .ical -> HTML -> PNG pipeline
The goal of this project is to take an ical, parse the next two weeks, convert it into various local timezones, and
produce a square image formatted to our needs for display in game. 

## What this does
1. Consume an existing .ical, convert it into representative timezones, 
and generate HTML in a pleasing format
  * Append this generated html to a spacing header to complete the format
2. Use Firefox in headless mode to generate 512x2048px images of the calendar in each locale
3. Manipulate the images using python-opencv to construct the calendar 1k square image, compliant with the scroll shader. 
4. [TODO] Encode each image into a single-frame mp4 
5. [TODO] upload to a cloud service of our choosing (gdrive)

## Steps in Unity

<ol start="5">
<li>Configure the unity project to discriminate between the user's locales</li>
<li>Use the users' locale to select the correct asset url</li>
<li>Rewrite the shader to work with 1k images instead of 4k images</li>
<li>Feed the correct url to the <a href="https://github.com/AoiKamishiro/VRC_UdonEventCalendar">Calendar Prefab</a></li>
</ol>


## References you need for this project:
Python3+
### Python Libraries (pip):
* ics
* opencv-python
* urllib3

### Fonts
Google's ["Noto Sans JP"]("https://fonts.google.com/specimen/Noto+Sans+JP") font needs to be extracted to the fonts/Noto_Sans_JP directory