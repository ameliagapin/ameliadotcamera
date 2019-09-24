#
# This script will read all jpg files in the provided directory and generate
# tags and pages for them. Photos show live in the static/photos directory.
#
# Usage: python3 createpages.py ../static/photos
#

import os, sys, fnmatch, errno, logging, datetime
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

def CreateShortcode(data):
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

    ret += " >}}"
    return ret

def GetData(sfile):
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
    data["shortcode"] = CreateShortcode(data)

    return data

def ProcessPhotos(files):
    global success, skipped
    photos = dict()
    photos[CHRONO_ALBUM] = []

    for sfile in files:
        try: 
            data = GetData(sfile)
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

def ConvertToSlug(keyword):
    slug = keyword.replace(" ", "-")
    slug = slug.lower()
    return slug

def CreatePosts(photos):
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
        slug = ConvertToSlug(key)
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
        thumb = "/photos/%s" % (value[0]["filename"])
        f.write("albumthumb: \"%s\"\n" % thumb)
        f.write("title: \"%s\"\n" % key)
        f.write("date: %s\n" % value[0]["date"].strftime(DATE_FORMAT))
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

    p = ProcessPhotos(photos)
    if len(p) == 0:
        print("No photos to create posts for.")
        sys.exit()
    CreatePosts(p)

    print("Total photos: ", total)
    print("Total tags: ", tags)
    print("Success photos: ", success)
    print("Skipped photos: ", skipped)
