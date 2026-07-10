# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#
# This script is part of the Intervalometerator project, a time-lapse camera controller for DSLRs:
# https://github.com/greiginsydney/Intervalometerator
# https://greiginsydney.com/intvlm8r
# https://intvlm8r.com
#
# This script incorporates code from python-gphoto2, and we are incredibly indebted to Jim Easterbrook for it.
# python-gphoto2 - Python interface to libgphoto2 http://github.com/jim-easterbrook/python-gphoto2 Copyright (C) 2015-17 Jim
# Easterbrook jim@jim-easterbrook.me.uk

"""
imageformat_map.py
Provided by Claude.ai, 10th July 2026

Restores friendly display labels for the Canon EOS 'imageformat' widget.

libgphoto2 2.5.32 changed the choice strings this widget reports - from
"Large Fine JPEG" to short codes like "L", "cL", "cM" etc. gphoto2 itself
still expects (and returns) these short codes, so we keep using them as
the actual dropdown VALUE, and only substitute a friendlier LABEL for
display. There's no old/new reconciliation needed: readRange() and
cameraPOST() already round-trip the same raw string within a single
GET/POST, so the raw value must stay untouched.
"""

IMAGE_FORMAT_LABELS = {
    'L'       : 'Large Fine JPEG',
    'cL'      : 'Large Normal JPEG',
    'M'       : 'Medium Fine JPEG',
    'cM'      : 'Medium Normal JPEG',
    'S1'      : 'Small Fine JPEG',
    'cS1'     : 'Small Normal JPEG',
    'S2'      : 'Small2 JPEG',
    'S3'      : 'Small3 JPEG',
    'RAW + L' : 'RAW + Large Fine JPEG',
    'RAW'     : 'RAW',
}


def getFriendlyImageFormat(rawChoice):
    """
    Takes a raw choice string as reported by the camera (e.g. 'cM') and
    returns a friendlier label for display (e.g. 'Medium Normal JPEG').
    Falls back to the raw string if it's not in the lookup table.
    """
    return IMAGE_FORMAT_LABELS.get(rawChoice, rawChoice)


def buildImgFmtOptions(rawOptions):
    """
    Takes the flat list of raw choice strings returned by readRange() and
    returns a list of (value, label) tuples for the template to loop over.
    'value' is always the untouched raw string, so cameraPOST() keeps
    setting exactly what the camera gave us. 'label' is just for display.
    """
    imgFmtOptions = []
    for choice in rawOptions:
        imgFmtOptions.append((choice, getFriendlyImageFormat(choice)))
    return imgFmtOptions
