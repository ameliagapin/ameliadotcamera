#!/usr/bin/env python

from PIL import Image
import os, sys, fnmatch

LONG_EDGE=2048

def ResizeImage(dest, infile):
    print("Processing: ", infile)

    name = os.path.basename(infile)
    outfile = dest + "/" + name

    if infile == outfile:
        return

    try:
        org = Image.open(infile)
        long = max(org.size[0], org.size[1])

        if (long > LONG_EDGE):
            open(outfile, "w+")

            if (org.size[0] > org.size[1]):
               width = LONG_EDGE
               height = int(round((LONG_EDGE/float(org.size[0]))*org.size[1]))
            else:
               height = LONG_EDGE
               width = int(round((LONG_EDGE/float(org.size[1]))*org.size[0]))

            new = org.resize((width, height), Image.ANTIALIAS)
        else:
            new = org

        new.save(outfile)
        print("Wrote resized file to  " + outfile)
    except:
        print("An error occured ",  sys.exc_info()[0])

if __name__=="__main__":
    if len(sys.argv) != 3:
        print("Must provide a source and a destination")
        sys.exit()

    source  = sys.argv[1]
    dest = sys.argv[2]

    if dest == "":
        print("Must provide a source and a destination")
        sys.exit()

    if not os.path.exists(dest):
        print(dest + " does not exist")
        sys.exit()

    # recursively loop through folders
    for root, dirs, files in os.walk(source):
       for file in files:
           file = file.lower()
           if fnmatch.fnmatch(file, '*.jpg'):
               file = root + "/" + file
               ResizeImage(dest, file)