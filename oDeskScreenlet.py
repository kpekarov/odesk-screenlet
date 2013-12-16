#!/usr/bin/env python

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

#  ExampleScreenlet (c) RYX 2007 <ryx@ryxperience.com>
#
# INFO:
# - a simple example for creating a Screenlet
# 
# TODO:
# - make a nice Screenlet from this example ;) ....

import screenlets
from screenlets.options import *
from screenlets.options import create_option_from_node
from screenlets import DefaultMenuItem
import pango
import gobject
import gtk
from datetime import datetime, timedelta

from odesk import Client
from odesk.utils import Query
from odesk.utils import Q

_ = screenlets.utils.get_translator(__file__)


class oDeskScreenlet(screenlets.Screenlet):
    """A simple example of how to create a Screenlet"""

    # default meta-info for Screenlets (should be removed and put into metainfo)
    __name__ = 'oDeskScreenlet'
    __version__ = '0.0.1+++'
    __author__ = 'Kirill Pekarov'
    __desc__ = __doc__    # set description to docstring of class
    __timeout = None
    text_colour = [1.0, 1.0, 1.0, 1.0]
    back_colour = [0, 0, 0, 1.0]
    show_image = True

    update_interval = 5
    odesk_key = ''
    odesk_secret = ''
    odesk_access_token_0 = ''
    odesk_access_token_1 = ''

    #keys = {'key': 'a4bf017a804d46a9695218f40a952e73', 'secret': '4493f04f50bbe387'}
    #keys['access_token_0'] = 'c664f9275a8871709ed6069dcc8aa07c'
    #keys['access_token_1'] = 'a7b6db2f1af73fe6'

    ODESK_WORKED_ON_FORMAT = '%Y%m%d'

    timereport_data = None

    def __init__(self, **keyword_args):
        # Create screenlet area
        screenlets.Screenlet.__init__(self, width=200, height=300, uses_theme=True, **keyword_args)

        self.theme_name = "default"

        self.add_options_group(_('Options'), _('Appearence Options'))
        self.add_option(ColorOption(_('Options'), 'text_colour', self.text_colour, _('Text Colour'), ''))
        self.add_option(ColorOption(_('Options'), 'back_colour', self.back_colour, _('Back Colour'), ''))

        self.add_options_group(_('oDesk'), _('oDesk Options'))
        self.add_option(IntOption('oDesk', 'update_interval',
                                  self.update_interval, 'Update interval:',
                                  'Update interval in minutes',
                                  min=5, max=360))
        self.add_option(StringOption('oDesk', 'odesk_key', '', 'API Key:', 'The oDesk API Key'))
        self.add_option(StringOption('oDesk', 'odesk_secret', '', 'API Secret:', 'The oDesk API Secret'), realtime=False)

        self.add_option(StringOption('oDesk', 'odesk_access_token_0', '', 'Access Token 1:', 'The oDesk API Token 0'))
        self.add_option(StringOption('oDesk', 'odesk_access_token_1', '', 'Access Token 2:', 'The oDesk API Token 1'))

        self.add_default_menuitems()
        self.update_interval = self.update_interval

    def get_client(self):
        """Authenticate using keys stored in ``keys.json`` and return
        the ``Client`` instance ready for work.

        """
        if len(self.odesk_key) > 0 and len(self.odesk_secret) > 0 \
            and len(self.odesk_access_token_0) > 0 and len(self.odesk_access_token_1) > 0:

            self.client = Client(self.odesk_key, self.odesk_secret,
                        oauth_access_token=self.odesk_access_token_0,
                        oauth_access_token_secret=self.odesk_access_token_1 )

    def get_auth_info(self):
        return self.client.get('https://www.odesk.com/api/auth/v1/info')

    def get_auth_user_uid(self):
        auth_info = self.get_auth_info()
        self.odesk_uid = auth_info['auth_user']['uid']

    def get_timereport(self, from_date=None, to_date=None):
        """Return parsed JSON data with timereport for given period.
        Fields are default.

        :from_date:    date object
        :to_date:      date object

        If empty - timereport from now to the begining of the current week.

        """

        if hasattr(self, 'client') is False:
            self.get_client()

        if hasattr(self, 'client'):
            now = datetime.now()
            if not to_date:
                to_date = now.date()
                if not from_date:
                    from_date = now.date() - timedelta(days=now.weekday())

            query = Query(
                select=Query.DEFAULT_TIMEREPORT_FIELDS,
                where=(Q('worked_on') >= from_date) & (Q('worked_on') <= to_date))

            self.get_auth_user_uid()

            return self.client.timereport.get_provider_report(self.odesk_uid, query)

    def get_today_and_this_week_times(self, data):
        """Return mapping of teams and hours worked for each team today
        and this week.

        :data:    parsed json data returned from ``get_timereport()`` function

        """
        now = datetime.now()

        date_idx = data['table']['cols'].index(
            {'type': 'date', 'label': 'worked_on'})
        team_idx = data['table']['cols'].index(
            {'type': 'string', 'label': 'team_name'})
        hours_idx = data['table']['cols'].index(
            {'type': 'number', 'label': 'hours'})

        teams = {}

        for row in data['table']['rows']:
            team_name = row['c'][team_idx]['v']
            hours = float(row['c'][hours_idx]['v'])
            date_worked_on = row['c'][date_idx]['v']
            if team_name not in teams:
                teams[team_name] = {'today_hours': 0.0, 'week_hours': 0.0}
            teams[team_name]['week_hours'] += hours
            if date_worked_on == now.strftime(self.ODESK_WORKED_ON_FORMAT):
                teams[team_name]['today_hours'] += hours
        return teams

    def get_timereport_layout(self, data):
        """Render text widged showing timereport data.

        :data:        parsed json data returned from ``get_timereport()`` function
        :odesk_uid:   oDesk user UID

        """
        row_template = '{0}:\n\t{1:.2f} hrs today\n\t{2:.2f} hrs this week\n'
        rows_rendered = '\n'.join(
            [row_template.format(team_name,
                                 team_data['today_hours'],
                                 team_data['week_hours'])
             for team_name, team_data
             in self.get_today_and_this_week_times(data).items()]
        )
        if not rows_rendered:
            rows_rendered = "\nNo worked hours yet"
        template = 'User: {odesk_uid}\n{rows}'
        return template.format(
            odesk_uid=self.odesk_uid,
            rows=rows_rendered
        )

    def on_draw(self, ctx):
        ctx.scale(self.scale, self.scale)

        if self.theme:
            data_start_position = 10
            data = self.get_timereport()
            if data is not None:
                data_text = self.get_timereport_layout(data)
            else:
                data_text = ''

            rectwidth = data_start_position + (len(data_text) * 13)
            # Background
            ctx.set_source_rgba(self.back_colour[0], self.back_colour[1], self.back_colour[2], 0.7)
            self.theme.draw_rounded_rectangle(ctx, 0, 0, 10, rectwidth, self.height, fill=True)

            # text
            if len(data_text) > 0:
                ctx.set_source_rgba(self.text_colour[0], self.text_colour[1], self.text_colour[2], 1.0)
                self.theme.draw_text(ctx, data_text, data_start_position, 23, 'Free Sans', 12, rectwidth - data_start_position,
                                     pango.ALIGN_LEFT)

    def on_draw_shape(self, ctx):
        self.on_draw(ctx)

    def show_edit_dialog(self):
        client = Client(self.odesk_key, self.odesk_secret)
        # create dialog
        dialog = gtk.Dialog(_("Verification Code"), self.window)
        dialog.resize(300, 200)

        link = gtk.LinkButton(format(client.auth.get_authorize_url()), "Press here and copy verification code here:")
        dialog.vbox.add(link)

        dialog.add_buttons(gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        entrybox = gtk.Entry()
        dialog.vbox.add(entrybox)

        dialog.show_all()
        # run dialog
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            verification_code = entrybox.get_text()
            self.odesk_access_token_0, self.odesk_access_token_1 = client.auth.get_access_token(verification_code)
        dialog.hide()
        self.update()

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
                if self.__timeout:
                    gobject.source_remove(self.__timeout)
                self.__timeout = gobject.timeout_add(value * 1000, self.update)
            else:
                pass
        elif name == "odesk_secret":
            if len(value) > 0 and len(self.odesk_key) > 0:
                self.__dict__['odesk_secret'] = value

                # if there is no tokens, show window with url and edit field
                # for enter verification code
                if len(self.odesk_access_token_0) == 0 or len(self.odesk_access_token_1) == 0:
                    self.show_edit_dialog()


# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
    # create new session
    import screenlets.session

    screenlets.session.create_session(oDeskScreenlet)

