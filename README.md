# Open Digital Frame

**Software to create a digital photo frame: browse image directories and do slideshows with image panning and cropping on-the-fly**

**Open Digital Frame** is a collection of Python programs and 
shell scripts to turn a GNU/Linux box into a digital photo 
frame. It was developed on a **Raspberry Pi version 2**, so it 
should run smoothly on very low-end hardware. Any GNU/Linux 
installation providing the **Python 3** interpreter and the 
**Qt5** library should be compatible with this software.

The project consists mainly of two programs: 
**open-digital-frame** and **photo-reframe**. The first one is a 
directory browser, where the directories are listed into a 
scrollable window, each with its thumbnail and title. The 
thumbnail is taken from a _folder.jpg_ file and metadata are 
read from a _folder.nfo_ file.

If a directory contains a **playlist.m3u** file and its 
thumbnail is selected (hit the Return key or double click), the 
**photo-reframe** program is started. This program will display 
each image listed into the playlist, performing panning and 
zooming on the fly as instructed by the playlist itself.

The directory browser **open-digital-frame** can be configured 
as an autostart program, it is also possible to configure a 
playlist as an autoplay item, so that the slideshow can start 
automatically when you turn on the system.

### open-digital-frame features

* Browse through pictures subdirectories using thumbnails and 
titles.
* Sort by sorttitle, directory name or data. Each subdirectory 
should contain a _folder.nfo_ file with the metadata.
* Launch the slideshow if a directory contains a _playlist.m3u_ 
file (there is a playlist symbol on the thumbnail).

![Screenshot of the directory browser.](/screenshots/odf-browser.png)

### photo-reframe features

* Pan and zoom each picture using the geometry saved into the 
playlist; no need to pre-process the images to fit the screen. 
Can use different playlists for different screen aspect ratio, 
eg. *playlist_16x9.m3u*, *playlist_4x3.m3u*, etc.
* Optionally show the Exif UserComment over the image as a 
subtitle.
* Optionally overlay Exif metadata of the photo (e.g. camera 
settings) over the image.
* Increase or decrease slide time.
* Stop the slideshow to change zoom and pan interactively.
* Update the playlist using the new framing settings.

![Slideshow with Exif metadata overlay](/screenshots/photo-reframe-exif-metadata.png)

## Operating system and additional packages required

Open Digital Frame was tested on the **Raspberry Pi OS 
desktop**, version Debian 12 Bookworm, release date December 5th 
2023. Beside the default installation of the operating system, 
some additional packages are required. Install them as root or 
using sudo:

```
apt install python3-pyqt5 exiv2
```

## Installation

To download and install Open Digital Frame, execute the 
following commands as root:

```
cd /usr/local/src
git clone https://github.com/RigacciOrg/open-digital-frame.git
cd open-digital-frame
make install
make install-utils
```

Several files are copied into the directories:

* **/usr/local/bin/**
* **/usr/local/lib/python3.11/dist-packages/open_digital_frame/**

Beside the two main programs **open-digital-frame** and 
**photo-reframe**, some other utilities are provided. They are 
Python or shell scripts and you can customize them as required.

* **photo-info** Extract Exif metadata from an image. Its output 
is used to overlay metadata on the image itself during the 
slideshow.
* **photo-share** During the slideshow you can press F2 to share 
the image with someone. This implementation requires an email 
address to send the current image as an attachment.
* **screensaver-off** Called before starting a slideshow, 
disable the scrensaver.
* **screensaver-on** Called when a slideshow is closed, to 
re-enable the screensaver.

## Configuration file

A configuration file example is provided: 
**[open-digital-frame.ini](/etc/open-digital-frame.ini)**. Here 
you can set the root folder containing the pictures, which 
defaults to **$HOME/Pictures/**.

The configuration file is searched into the current directory or 
it is received as the first parameter:

```
open-digital-frame /home/pi/.config/open-digital-frame.ini
```

## The directory folder.nfo file

The directory browser of Open Digital Frame searches for a 
**folder.nfo** file into each subdirectory. The file is a simple 
XML file that may contains some tags; these tags are used to 
compose the thumbnails screen, to sort items and to select 
playlists to play by tags.

This is an example:

```
<slideshow>
    <title>Libera Università di Alcatraz - Luglio 2012</title>
    <sorttitle>2012_07_16_</sorttitle>
    <tag>Family</tag>
    <tag>Holydays</tag>
    <date>2012-07-16</date>
</slideshow>
```

## The directory thumbnails

If a directory contains a **folder.jpg** or **folder.png**, that 
image is used as a thumbnails into the Open Digital Frame 
directory browser.

## How to create the playlist_16x9.m3u files

The playlist is a text file saved into the directory that
contains the images. The default, preferred name is
**playlist_16x9.m3u**, other names searched for are
**playlist_4x3.m3u** and **playlist.m3u**.

You can set the playlist filename preferences into the
open-digital-frame configuration file.

The playlist contains the filename of the images and their
respective geometries, separated by a vertical bar, something
like this:

```
IMG_6602.JPG|4000x2250+0+332
IMG_6605.JPG|2971x1671+796+628
IMG_6606.JPG|4000x2250+0+442
IMG_6610.JPG|3810x2143+90+387
IMG_6615.JPG|2828x1590+547+681
IMG_6617.JPG|1633x918+1229+1052
IMG_6624.JPG|2843x1599+393+585
```

Each geometry determines the portion of the image to be shown in
the slideshow, and it is composed by four values:

* **width** of the crop region
* **height** of the crop region
* **X offset** of the top-left corner of the region
* **Y offset** of the top-left corner of the region

The cropped region is resized to occupy the entire screen.

The playlist file can be created manually, but the preferred way 
is to use the **photo-reframe** program interactively: using a 
keyboard you can cycle through all the images contained into a 
directory, zoom and pan each photo as required and finally save 
the updated playlist. Here it is an example:

```
cd Picture/Holydays
photo-reframe .
```
The keys to use are:

* **F** or **F11**: to toggle full screen
* **+** or **-**: zoom in or out
* **Arrows keys**: pan
* **Return**: confirm the geometry for the current image
* **Space**: move to the next image
* **Backspace**: move to the previous image
* **S**: save the playlist
* **F1**: help on keys function

If you re-run the program, the existing playlist is loaded and 
it is possible to make further changes to it.
