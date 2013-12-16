#!/usr/bin/python

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

# UptimeScreenlet (c) spdf (aka Mark Hayes) 2008 <mcleodm@gmail.com>

import os
import screenlets
from screenlets import Screenlet
from screenlets.options import ColorOption, BoolOption
import cairo
import pango
import gobject

# use gettext for translation
import gettext

_ = screenlets.utils.get_translator(__file__)


def tdoc(obj):
    obj.__doc__ = _(obj.__doc__)
    return obj


@tdoc
class UptimeScreenlet(screenlets.Screenlet):
    """Simple Uptime Screenlet"""
    __name__ = 'UptimeScreenlet'
    __version__ = '0.1.2+++'
    __author__ = 'spdf'
    __desc__ = __doc__
    __timeout = None
    text_colour = [1.0, 1.0, 1.0, 1.0]
    back_colour = [0, 0, 0, 1.0]
    show_image = True

    update_interval = 1

    def __init__(self, **keyword_args):
        # Create screenlet area
        screenlets.Screenlet.__init__(self, width=700, height=72, uses_theme=True, **keyword_args)

        self.theme_name = "default"
        self.update_interval = self.update_interval

        self.add_options_group(_('Options'), _('Appearence Options'))
        self.add_option(ColorOption(_('Options'), 'text_colour', self.text_colour, _('Text Colour'), ''))
        self.add_option(ColorOption(_('Options'), 'back_colour', self.back_colour, _('Back Colour'), ''))
        self.add_option(BoolOption(_('Options'), 'show_image', self.show_image, _('Show image'), ''))

    def uptime(self):
        try:
            f = open("/proc/uptime")
            contents = f.read().split()
            f.close()
        except:
            return _("Cannot open uptime file: /proc/uptime")

        total_seconds = float(contents[0])

        # Helper vars:
        MINUTE = 60
        HOUR = MINUTE * 60
        DAY = HOUR * 24

        # Get the days, hours, etc:
        days = int(total_seconds / DAY)
        hours = int(( total_seconds % DAY ) / HOUR)
        minutes = int(( total_seconds % HOUR ) / MINUTE)
        seconds = int(total_seconds % MINUTE)

        # Build up the pretty string (like this: "N days, N hours, N minutes, N seconds")
        string = ""
        if days > 0:
            string += str(days) + " " + (days == 1 and _("day") or _("days") ) + ", "
        if len(string) > 0 or hours > 0:
            string += str(hours) + " " + (hours == 1 and _("hour") or _("hours") ) + ", "
        if len(string) > 0 or minutes > 0:
            string += str(minutes) + " " + (minutes == 1 and _("minute") or _("minutes") ) + ", "

        string += str(seconds) + " " + (seconds == 1 and _("second") or _("seconds") )
        return string;

    def on_init(self):
        self.add_default_menuitems()

    def on_draw(self, ctx):
        ctx.scale(self.scale, self.scale)

        if (self.theme):
            uptime_val = self.uptime()
            if (self.show_image):
                uptime_start = 44
            else:
                uptime_start = 10

            rectwidth = uptime_start + (len(uptime_val) * 13)
            # Background
            ctx.set_source_rgba(self.back_colour[0], self.back_colour[1], self.back_colour[2], 0.7)
            self.theme.draw_rounded_rectangle(ctx, 0, 0, 10, rectwidth, self.height, fill=True)

            # Uptime text
            ctx.set_source_rgba(self.text_colour[0], self.text_colour[1], self.text_colour[2], 1.0)
            self.theme.draw_text(ctx, uptime_val, uptime_start, 23, 'Free Sans', 20, rectwidth - uptime_start,
                                 pango.ALIGN_LEFT)

            # "UPTIME"
            if (self.show_image):
                ctx.translate(4, 4)
                self.theme.render(ctx, 'uptime')

    def on_draw_shape(self, ctx):
        self.on_draw(ctx)

    def update(self):
        gobject.idle_add(self.redraw_canvas)
        return True

    def __setattr__(self, name, value):
        # call Screenlet.__setattr__ in baseclass
        screenlets.Screenlet.__setattr__(self, name, value)

        # check for this Screenlet's attributes, we are interested in:
        if name == "update_interval":
            if value > 0:
                self.__dict__['update_interval'] = value
                if (self.__timeout):
                    gobject.source_remove(self.__timeout)
                self.__timeout = gobject.timeout_add(value * 1000, self.update)
            else:
                pass


if __name__ == "__main__":
    #Create screenlet session
    import screenlets.session

    screenlets.session.create_session(UptimeScreenlet)
