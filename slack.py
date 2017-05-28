# Name: slack.py
# Author: pbzweihander
# Email: sd852456@naver.com
#
# Copyright (C) 2017 pbzweihander
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

from slackclient import SlackClient


class Slack:
    client = None
    name = ""
    id = ""
    connected = False
    users = dict()

    def __init__(self, token: str, name: str):
        self.client = SlackClient(token)
        self.name = name

        api_call = self.client.api_call("users.list")
        if api_call.get('ok'):
            self.users = api_call.get('members')
            for user in self.users:
                if 'name' in user and user.get('name') == self.name:
                    self.id = user.get('id')
                    break

    def refresh_users(self):
        for u in self.client.api_call("users.list").get('members'):
            self.users[u.get('id')] = u.get('name')

    def connect(self) -> bool:
        self.connected = self.client.rtm_connect()
        return self.connected

    @staticmethod
    def parse_slack_output(output: list) -> dict:
        if output and len(output) > 0:
            for o in output:
                if o and 'text' in o:
                    return o
        return {}

    def post_message(self, chan: str, msg: str, as_user=True, name=""):
        if self.connected:
            self.client.api_call('chat.postMessage', channel=chan, text=msg, as_user=as_user, username=name)

    def read(self) -> dict:
        if self.connected:
            return self.parse_slack_output(self.client.rtm_read())
