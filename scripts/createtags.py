import logging
import datetime
import os
import shutil
from iptcinfo3 import IPTCInfo

iptcinfo_logger = logging.getLogger('iptcinfo')
iptcinfo_logger.setLevel(logging.ERROR)

CHRONO_ALBUM = "latest"
CONTENT_DIRECTORY = "../content/tag/"
ENCODING = "utf-8"
DATE_FORMAT = "%Y-%m-%d"

files = [
    "../static/photos/2019/03/photo-6.jpg",
    "../static/photos/2019/03/photo-5.jpg",
    "../static/photos/2019/03/photo-4.jpg",
    "../static/photos/2019/03/photo-3.jpg",
    "../static/photos/2019/03/photo-2.jpg",
    "../static/photos/2019/03/photo.jpg",
]

def CreateShortcode(data):
    ret = "{{< photo"
    ret += " full=\"/photos/%04d/%02d/%s\"" % (data["date"].year, data["date"].month, data["filename"])
    ret += " thumb=\"/photos/%04d/%02d/%s\"" % (data["date"].year, data["date"].month, data["filename"])
    ret += " date=\"%s\"" % data["date"].strftime(DATE_FORMAT)

    if "title" in data:
        ret += " phototitle=\"%s\"" % data["title"]
    if "description" in data:
        ret += " description=\"%s\"" % data["description"]
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
        data["title"] = title
    desc = info["caption/abstract"]
    if desc:
        data["description"] = desc.decode(ENCODING)
    date = info["date created"]
    if date:
        date_obj = datetime.datetime.strptime(date.decode(ENCODING), '%Y%m%d')
        data["date"] = date_obj
    if info["keywords"]:
        data["keywords"] = []
        for key in info["keywords"]:
            data["keywords"].append(key.decode(ENCODING))
    data["shortcode"] = CreateShortcode(data)

    return data

def ProcessPhotos(files):
    photos = dict()
    photos[CHRONO_ALBUM] = []

    for sfile in files:
        data = GetData(sfile)
        photos[CHRONO_ALBUM].append(data)
    photos[CHRONO_ALBUM].sort(key=lambda x: x["date"], reverse=True)

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

def CreateFiles(photos):
    try:
        shutil.rmtree(CONTENT_DIRECTORY)
        os.makedirs(CONTENT_DIRECTORY)
    except OSError:
        raise

    for key, value in photos.items():
        slug = ConvertToSlug(key)
        path = "%s%s" % (CONTENT_DIRECTORY, slug)

        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        file = "%s/_index.md" % path
        f = open(file,"w+")

        f.write("---\n")
        f.write("albumthumb: \"%s\"\n" % value[0]["path"])
        f.write("title: \"%s\"\n" % key)
        f.write("date: %s\n" % value[0]["date"].strftime(DATE_FORMAT))
        f.write("---\n")

        for photo in value:
            f.write("%s\n" % photo["shortcode"])

        f.close()


photos = ProcessPhotos(files)
CreateFiles(photos)
