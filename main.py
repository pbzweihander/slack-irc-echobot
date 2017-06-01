
from irc import IRC
from slack import Slack
from threading import Thread
from settings import *


irc = IRC()
slack = Slack(SLACK_TOKEN, BOT_NAME)


class IRCThread(Thread):
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
                if text.startswith("PING"):
                    irc.raw_send('PONG ' + text[5:])
                else:
                    prefix = text.find('PRIVMSG #%s :' % IRC_CHANNEL)
                    len_prefix = len('PRIVMSG #%s :' % IRC_CHANNEL)
                    if prefix != -1:
                        msg = text[prefix + len_prefix:]
                        for uid in slack.users:
                            msg = msg.replace('<@' + uid + '>', '<@' + slack.users[uid] + '>')
                        username = text[1:text.find('!')]
                        slack.post_message('#' + SLACK_CHANNEL, msg, False, username)
                        print("irc -> slack - " + username + ": " + msg)
        print("IRC Reading Thread Suspended")


class SlackThread(Thread):
    __suspend = False

    def __init__(self):
        Thread.__init__(self)
        print("Slack Reading Thread __init__")

    def suspend(self):
        self.__suspend = True

    def run(self):
        print("Slack Reading Thread run")
        while not self.__suspend:
            texts = slack.read()
            for d in texts:
                if d.get('type') == 'message' and 'subtype' not in d:
                    if slack.channels.get(d.get('channel')) == SLACK_CHANNEL:
                        userid = d.get('user')
                        username = slack.users.get(userid)
                        if not username:
                            slack.refresh_users()
                            username = slack.users.get(userid) or "?"
                        msg = d.get('text')
                        for uid in slack.users:
                            msg = str.replace(msg, '<@' + uid + '>', '<@' + slack.users[uid] + '>')
                        msg = str.replace(msg, '&lt;', '<').replace('&gt;', '>')
                        irc.send(IRC_CHANNEL, username + ": " + msg)
                        print("slack -> irc - " + username + ": " + msg)
        print("Slack Reading Thread Suspended")


def main():
    irc.init()
    irc.connect(IRC_SERVER, IRC_PORT, IRC_CHANNEL, BOT_NAME)
    slack.connect()

    print("Clients Loaded")

    irc_thread = IRCThread()
    slack_thread = SlackThread()

    print("Thread Initialized")

    irc_thread.start()
    slack_thread.start()

    while True:
        try:
            pass
        except KeyboardInterrupt:
            break

    print("Suspending All Threads...")

    irc_thread.suspend()
    slack_thread.suspend()


if __name__ == '__main__':
    main()
