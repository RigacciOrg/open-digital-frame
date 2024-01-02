# open-digital-frame
Software to create a digital photo frame: browse image directories and do slideshows with image panning and cropping on-the-fly

## Directory nfo file

```
```

## Playlist Format

The playlist is a text file saved into the directory that
contains the images. The default, preferred name is
**playlist_16x9.m3u**, other names searched for are
**playlist_16x9.m3u** and **playlist.m3u**.

You can set the playlist filename preferences into the
configuration file.

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
