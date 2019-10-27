#
# This script will read all jpg files in the provided directory and generate
# tags and pages for them. Photos show live in the static/photos directory.
#
# Usage: python3 createpages.py ../static/photos
#

import os, sys, fnmatch, errno, logging, datetime, random, exifread
import shutil
from iptcinfo3 import IPTCInfo

iptcinfo_logger = logging.getLogger('iptcinfo')
iptcinfo_logger.setLevel(logging.ERROR)

CHRONO_ALBUM = "latest"
CONTENT_DIRECTORY = "../content/tag/"
ENCODING = "utf-8"
DATE_FORMAT = "%Y-%m-%d"

total = 0
tags = 0
success = 0
skipped = 0

def get_shortcode(data):
    ret = "{{< photo"
    ret += " full=\"/photos/%s\"" % (data["filename"])
    ret += " thumb=\"/photos/%s\"" % (data["filename"])
    if "date" in data:
        ret += " date=\"%s\"" % data["date"].strftime(DATE_FORMAT)
    if "title" in data:
        ret += " phototitle=\"%s\"" % data["title"]
    if "description" in data:
        desc = data["description"]
        ret += " description=\"%s\"" % desc
    if "keywords" in data:
        ret += " tags=\"%s\"" % ",".join(data["keywords"])
    ret += " camera=\"%s\"" % format_exif(data)
    ret += " >}}"

    return ret

def format_exif(data):
    camera = ""
    if "model" in data:
        camera += data["model"]
    else:
        return""

    if "focal" in data:
        camera += " at " + data["focal"] + "mm"
    if "aperture" in data:
        camera += " f/" + data["aperture"]
    if "shutter" in data:
        camera += " " + data["shutter"] + "s"
    if "iso" in data:
        camera += " ISO " + data["iso"]

    return camera

def get_img_data(sfile):
    try:
        info = IPTCInfo(sfile)
    except:
        logging.ERROR("Could not open file: %s" % sfile)

    data = dict()

    data["path"] = sfile
    data["filename"] = os.path.basename(sfile)

    title = info["object name"] or info["headline"]
    if title:
        data["title"] = title.decode(ENCODING)
    desc = info["caption/abstract"]
    if desc:
        data["description"] = desc.decode(ENCODING)
    date = info["date created"]
    if date:
        date_obj = datetime.datetime.strptime(date.decode(ENCODING), '%Y%m%d')
        data["date"] = date_obj
    data["keywords"] = []
    if info["keywords"]:
        for key in info["keywords"]:
            data["keywords"].append(key.decode(ENCODING))

    # exif
    exif = get_exif(sfile)
    for tag in exif.keys():
        value = str(exif[tag])
        if tag == "Image Model":
            data["model"] = value
        if tag == "EXIF ExposureTime":
            data["shutter"] = value
        if tag == "EXIF FocalLength":
            data["focal"] = value
        if tag == "EXIF FNumber":
            data["aperture"] = str(parse_fstop(value))
        if tag == "EXIF ISOSpeedRatings":
            data["iso"] = value
        if tag == "EXIF LensModel":
            data["lens"] = value

    data["shortcode"] = get_shortcode(data)

    return data

def get_exif(path):
    f = open(path, 'rb')
    exif = exifread.process_file(f, details=False)
    return exif

def parse_fstop(fraction):
    try:
        return float(fraction)
    except ValueError:
        num, denom = fraction.split('/')
        try:
            leading, num = num.split(' ')
            whole = float(leading)
        except ValueError:
            whole = 0
        frac = float(num) / float(denom)
        return whole - frac if whole < 0 else whole + frac

def process_photos(files):
    global success, skipped
    photos = dict()
    photos[CHRONO_ALBUM] = []

    for sfile in files:
        try: 
            data = get_img_data(sfile)
        except:
            skipped += 1
            print("Failed to process file: " + sfile)
            print(sys.exc_info())
            continue
        if not set(("date", "path", "filename")).issubset(data):
            skipped += 1
            print("Missing metadata for: " + sfile)
            continue
        # All photos get added to the chronological album
        photos[CHRONO_ALBUM].append(data)
        success += 1

    # We need this reverse chronological
    photos[CHRONO_ALBUM].sort(key=lambda x: x["date"], reverse=True)

    # With all photos processed and in chrono album
    # we can iterate through and add photos to each of their
    # tags' albums
    for photo in photos[CHRONO_ALBUM]:
        for kw in photo["keywords"]:
            if not kw in photos:
                photos[kw] = []
            photos[kw].append(photo)
    return photos

def get_slug(keyword):
    slug = keyword.replace(" ", "-")
    slug = slug.lower()
    return slug

def create_posts(photos):
    try:
        shutil.rmtree(CONTENT_DIRECTORY)
        os.makedirs(CONTENT_DIRECTORY)
    except OSError:
        raise

    global tags, success

    # iterate over tags
    for key, value in photos.items():
        if len(value) == 0:
            continue
        slug = get_slug(key)
        path = "%s%s" % (CONTENT_DIRECTORY, slug)

        print("Processing tag: %s (%s)" % (slug, len(value)))

        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        # create index file for tag
        file = "%s/_index.md" % path
        f = open(file,"w+")

        f.write("---\n")
        thumb_index = 0
        if key is not 'latest' and len(value)>1:
            thumb_index = random.randrange(0, len(value)-1)
        thumb = "/photos/%s" % (value[thumb_index]["filename"])
        f.write("albumthumb: \"%s\"\n" % thumb)
        f.write("title: \"%s\"\n" % key)
        f.write("date: %s\n" % value[thumb_index]["date"].strftime(DATE_FORMAT))
        f.write("---\n")

        # iterate over photos for tag
        for photo in value:
            f.write("%s\n" % photo["shortcode"])

        f.close()
        tags += 1

if __name__=="__main__":
    source = sys.argv[1]

    photos  = []

    # recursively loop through folders
    for root, dirs, files in os.walk(source):
       for file in files:
           file = file.lower()
           if fnmatch.fnmatch(file, '*.jpg'):
               file = root + "/" + file
               photos.append(file)
               total += 1

    p = process_photos(photos)
    if len(p) == 0:
        print("No photos to create posts for.")
        sys.exit()

    create_posts(p)

    print("Total photos: ", total)
    print("Total tags: ", tags)
    print("Success photos: ", success)
    print("Skipped photos: ", skipped)
