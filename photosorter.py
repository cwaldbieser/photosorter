#! /usr/bin/env python

from __future__ import print_function

import argparse
import os
import os.path
import sys

import exifread
from dateutil.parser import parse as dateparse


def get_image_date(path):
    """
    Given the path to an image file, try to determine the date the
    image was taken.
    """
    with open(path, "rb") as f:
        try:
            tags = exifread.process_file(f, details=False)
        except IOError:
            return None
        if "Image DateTime" in tags:
            return tags["Image DateTime"].values
        elif "EXIF DateTimeDigitized" in tags:
            return tags["EXIF DateTimeDigitized"].values
        else:
            return None


def process_file(path, args):
    dry_run = args.dry_run
    move_photos = args.move_photos
    dt = get_image_date(path)
    if dt is None:
        print(
            "Could not extract date for '{0}'.  Skipping ...".format(path),
            file=sys.stderr,
        )
        return
    if not hasattr(dt, "strftime"):
        dt_part, time_part = dt.split()
        dt_part = dt_part.replace(":", "-")
        combined = "{0} {1}".format(dt_part, time_part)
        try:
            dt = dateparse(combined)
        except ValueError:
            print(
                "Odd date data: '{0}' for '{1}'.  Skipping ...".format(str(dt), path),
                file=sys.stderr,
            )
            return
    s = dt.strftime("%Y-%m-%d")
    dst_dir = os.path.join(args.dest_dir, s)
    dst_path = os.path.join(dst_dir, os.path.basename(path))
    if dry_run:
        print("{0} -> {1}".format(path, dst_path))
    else:
        if not os.path.exists(dst_dir):
            os.mkdir(dst_dir)
        if not os.path.exists(dst_path):
            if move_photos:
                os.rename(path, dst_path)
            else:
                os.symlink(path, dst_path)
        else:
            print("File exists: '{0}'".format(dst_path), file=sys.stderr)


def process_tree(photo_dir, args):
    for dirpath, dirnames, filenames in os.walk(photo_dir):
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            process_file(path, args)


def process_dir(photo_dir, args):
    entries = os.listdir(photo_dir)
    for entry in entries:
        path = os.path.join(photo_dir, entry)
        if os.path.isfile(path):
            process_file(path, args)


def main(args):
    recurse = args.recurse
    paths = args.photos
    for path in paths:
        if os.path.isdir(path):
            if recurse:
                process_tree(path, args)
            else:
                process_dir(path, args)
        else:
            process_file(path, args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Photo Sorter")
    parser.add_argument(
        "photos",
        nargs="+",
        help="Directories or that contains photos to be sorted or individual photos.",
    )
    parser.add_argument(
        "--dest-dir",
        default="/home/carl/Pictures/photos/dates",
        help="Destination folder.",
    )
    parser.add_argument(
        "-r", "--recurse", action="store_true", help="Recurse into subdirectories."
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Do not sort photos.  Report how they would be sorted.",
    )
    parser.add_argument(
        "--move-photos",
        action="store_true",
        help="Move the files.  Default is to sym-link them.",
    )
    args = parser.parse_args()
    main(args)
