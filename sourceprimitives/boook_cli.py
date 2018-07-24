# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2018, Galen Curwen-McAdams

import argparse
import itertools
import random
import subprocess
from sourceprimitives import boook

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", default="boook", help="")
    parser.add_argument("--section", default=None, action="append", nargs=3, metavar=('name', 'amount', 'numeration'), help="")
    parser.add_argument("--output-path", default=".", help="")
    parser.add_argument("--manifest", default=None, nargs="+", choices=["csv"], help="")
    parser.add_argument("--verbose", action="store_true", help="")
    parser.add_argument("--dry-run", action="store_true", help="generate manifests, but not image files")
    parser.add_argument("--rotate", nargs="+", type=int, help="rotation values to cycle through. Uses imagemagick to rotate")
    parser.add_argument("--rotate-jitter", type=int, default=0, help="random jitter added to rotation")

    args = parser.parse_args()
    # special sections "toc" and "index"
    # for example:
    # toc 1 partial
    # index 5 partial

    # validate section metavars, should probably
    # be done using argparse machinery
    for section_num, section in enumerate(args.section):
        title, amount, numeration = section
        try:
            args.section[section_num][1] = int(amount)
        except:
            raise argparse.ArgumentTypeError("value must be Integer")
        try:
            if numeration != "full" or numeration != "partial":
                   args.section[section_num][2] = "full"
        except:
            pass

    # generate boook
    b = boook.Boook(args.title, args.section, manifest_formats=args.manifest, verbose_output=args.verbose, dry_run=args.dry_run, output_directory=args.output_path)
    generated_files = b.generate()

    if args.rotate:
        rotations = itertools.cycle(args.rotate)
        rotation = int(next(rotations))
        for file in generated_files:
            jitter = random.randint(0, args.rotate_jitter)
            rotation += jitter
            if args.verbose:
                print("rotating {} to {} (jitter: {})".format(file, rotation, jitter))
            # use mogrify to rotate files inplace
            subprocess.call(["mogrify", "-rotate", str(rotation), file])
            rotation = int(next(rotations))
