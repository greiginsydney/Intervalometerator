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

# This test script is from https://github.com/jim-easterbrook/python-gphoto2/issues/30, provided by user birkanozer

import gphoto2 as gp

context = gp.Context()
camera = gp.Camera()
camera.init(context)
config_tree = camera.get_config(context)
print('=======')

total_child = config_tree.count_children()
for i in range(total_child):
    child = config_tree.get_child(i)
    text_child = (f'# {child.get_label()} {child.get_name()}')
    print(text_child)

    for a in range(child.count_children()):
        grandchild = child.get_child(a)
        text_grandchild = (f'    * {grandchild.get_label()} -- {grandchild.get_name()}')
        print(text_grandchild)

        try:
            text_grandchild_value = (f'        Setted: {grandchild.get_value()}')
            print(text_grandchild_value)
            print('        Possibilities:')
            for k in range(grandchild.count_choices()):
                choice = grandchild.get_choice(k)
                text_choice = (f'         - {choice}')
                print(text_choice)
        except:
            pass
        print()
    print()

camera.exit(context)
