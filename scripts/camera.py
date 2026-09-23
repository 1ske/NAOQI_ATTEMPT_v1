#!/usr/bin/env python
"""Grab one image from the top camera and save it as a PNG. Needs naoqisim without -nocam."""
from __future__ import print_function

import os

from PIL import Image

from common import parse_args, proxies

K_TOP, K_BOTTOM = 0, 1
K_QVGA, K_VGA = 1, 2
K_RGB = 11


def extra(parser):
    parser.add_argument("--camera", type=int, default=K_TOP, help="0 top, 1 bottom")
    parser.add_argument("--resolution", type=int, default=K_VGA, help="1 QVGA, 2 VGA")
    parser.add_argument("--out", default="out/camera.png")

args = parse_args(__doc__, extra)
video = proxies(args, "ALVideoDevice")["ALVideoDevice"]

handle = video.subscribeCamera("naoqi_basics_camera", args.camera, args.resolution, K_RGB, 5)
try:
    image = video.getImageRemote(handle)
    if image is None:
        raise SystemExit("no image (is naoqisim running with -nocam?)")
    width, height, data = image[0], image[1], image[6]
    out_dir = os.path.dirname(args.out)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    Image.frombytes("RGB", (width, height), bytes(data)).save(args.out)
    print("saved %dx%d image to %s" % (width, height, args.out))
finally:
    video.unsubscribe(handle)
