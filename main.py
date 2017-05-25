
from irc import IRC
from slack import Slack
from threading import Thread
from queue import Queue
from settings import *


irc = IRC()
slack = Slack(SLACK_TOKEN, BOT_NAME)
irc_queue = Queue()
slack_queue = Queue()

irc_channel_to_echo = ""
irc_nicknames_to_ignore = []
slack_channel_to_echo = ""
slack_nicknames_to_ignore = []


class IRCReadingThread(Thread):
    __suspend = False

    def __init__(self):
        Thread.__init__(self)
        print("IRC Reading Thread __init__")

    def suspend(self):
        self.__suspend = True

    def run(self):
        print("IRC Reading Thread run")
        while not self.__suspend:
            lines = irc.get_text()
            for text in lines:
                if not text:
                    continue

                if 'PING ' in text:
                    irc.raw_send('PONG ' + text.split()[1])
                elif 'INVITE ' in text:  # 유저가 채널로 초대시 응답
                    irc.join(text.split(':', 2)[-1])
                elif 'PRIVMSG ' in text:
                    chan = text.split("PRIVMSG ")[1].split()[0]
                    sender = text.split("!")[0][1:]
                    msg = text.split(":", 2)[2]

                    if "#" in chan:
                        irc_queue.put((chan, sender, msg))
        print("IRC Reading Thread Suspended")


class SlackReadingThread(Thread):
    __suspend = False

    def __init__(self):
        Thread.__init__(self)
        print("Slack Reading Thread __init__")

    def suspend(self):
        self.__suspend = True

    def run(self):
        print("Slack Reading Thread run")
        while not self.__suspend:
            d = slack.read()
            if d and d.get('subtype') != "bot_message" and d.get('user') != slack.id:
                userid = d.get('user')
                username = [u.get('name') for u in slack.users if u.get('id') == userid]
                if not username:
                    slack.refresh_users()
                    username = [u.get('name') for u in slack.users if u.get('id') == userid]
                if username:
                    username = username[0]
                else:
                    username = "?"
                chan = d.get('channel')
                msg = d.get('text')
                slack_queue.put((chan, username, msg))
        print("Slack Reading Thread Suspended")


class IRCHandlingThread(Thread):
    __suspend = False

    def __init__(self):
        Thread.__init__(self)
        print("IRC Handling Thread __init__")

    def suspend(self):
        self.__suspend = True

    def run(self):
        global irc_channel_to_echo, irc_nicknames_to_ignore
        print("IRC Handling Thread run")
        while not self.__suspend:
            if not irc_queue.empty():
                t = irc_queue.get()
                chan = t[0]
                name = t[1]
                msg = t[2]

                if str.startswith(msg, '?setechohere'):
                    irc_channel_to_echo = chan
                    irc.send(chan, "! Echo here")
                    print("IRC Channel Set : " + chan)
                else:
                    if irc_channel_to_echo and chan == irc_channel_to_echo:
                        if str.startswith(msg, '?setignore'):
                            for n in str.split(msg, '?setignore')[1].strip().split():
                                irc_nicknames_to_ignore.append(n)
                                irc.send(chan, "! Ignore " + n)
                                print("IRC Ignore Set : " + n)
                        elif str.startswith(msg, '?unsetignore'):
                            for n in str.split(msg, '?unsetignore')[1].strip().split():
                                if n in irc_channel_to_echo:
                                    irc_nicknames_to_ignore.remove(n)
                                    irc.send(chan, "! Do not ignore " + n)
                                    print("IRC Ignore Unset : " + n)
                        else:
                            if name not in irc_nicknames_to_ignore:
                                if slack_channel_to_echo:
                                    # outname = chr(8203).join(name)
                                    # slack.post_message(slack_channel_to_echo, outname + ": " + msg)
                                    # slack.post_message(slack_channel_to_echo, name + ": " + msg)
                                    slack.post_message(slack_channel_to_echo, msg, False, name)
                                    print("irc -> slack - " + name + ": " + msg)
        print("IRC Handling Thread Suspended")


class SlackHandlingThread(Thread):
    __suspend = False

    def __init__(self):
        Thread.__init__(self)
        print("Slack Handling Thread __init__")

    def suspend(self):
        self.__suspend = True

    def run(self):
        global slack_channel_to_echo, slack_nicknames_to_ignore
        print("Slack Handling Thread run")
        while not self.__suspend:
            if not slack_queue.empty():
                t = slack_queue.get()
                chan = t[0]
                name = t[1]
                msg = t[2]

                if str.startswith(msg, '?setechohere'):
                    slack_channel_to_echo = chan
                    slack.post_message(chan, "! Echo here")
                    print("Slack Channel Set : " + chan)
                else:
                    if slack_channel_to_echo and chan == slack_channel_to_echo:
                        if str.startswith(msg, '?setignore'):
                            for n in str.split(msg, '?setignore')[1].strip().split():
                                slack_nicknames_to_ignore.append(n)
                                slack.post_message(chan, "! Ignore " + n)
                                print("Slack Ignore Set : " + n)
                        elif str.startswith(msg, '?unsetignore'):
                            for n in str.split(msg, '?unsetignore')[1].strip().split():
                                if n in slack_nicknames_to_ignore:
                                    slack_nicknames_to_ignore.remove(n)
                                    slack.post_message(chan, "! Do not ignore " + n)
                                    print("Slack Ignore Unset : " + n)
                        else:
                            if name not in slack_nicknames_to_ignore:
                                if irc_channel_to_echo:
                                    # outname = chr(8203).join(name)
                                    # irc.send(irc_channel_to_echo, outname + ": " + msg)
                                    irc.send(irc_channel_to_echo, name + ": " + msg)
                                    print("slack -> irc - " + name + ": " + msg)
        print("Slack Handling Thread Suspended")


def main():
    irc.init()
    irc.connect(IRC_SERVER, IRC_PORT, IRC_CHANNEL, BOT_NAME)
    slack.connect()

    print("Clients Loaded")

    irc_reading_thread = IRCReadingThread()
    irc_handling_thread = IRCHandlingThread()
    slack_reading_thread = SlackReadingThread()
    slack_handling_thread = SlackHandlingThread()

    print("Thread Initialized")

    irc_reading_thread.start()
    slack_reading_thread.start()
    irc_handling_thread.start()
    slack_handling_thread.start()

    while True:
        try:
            pass
        except KeyboardInterrupt:
            break

    print("Suspending All Threads...")

    irc_reading_thread.suspend()
    irc_handling_thread.suspend()
    slack_reading_thread.suspend()
    slack_handling_thread.suspend()


if __name__ == '__main__':
    main()
