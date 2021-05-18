# .ical to HTML converter
The first step of this task is to consume an existing .ical, convert it into representative timezones, 
and produce HTML that meets our standards for formatting. 

## What's next
Next steps in this task list are the following:

1. Complete the calendar header
2. Automate image generation of the calendar in each locale. (Will likely use firefox in headless mode for this)
3. Manipulate the images using python-opencv to construct the calendar 1k (or 2k) square image, compliant with the scroll shader. 
4. Encode each image into a single-frame mp4 and upload to a cloud service of our choosing (gdrive)

## Steps in Unity

<ol start="5">
<li>Configure the unity project to discriminate between the user's locales</li>
<li>Use the users' locale to select the correct asset url</li>
<li>Feed the correct url to the <a href="https://github.com/AoiKamishiro/VRC_UdonEventCalendar">Calendar Prefab</a></li>
</ol>