import irc_wrapper
import slack_wrapper
import settings
import threading
import time
import json


irc = irc_wrapper.IRC()
slack = slack_wrapper.Slack(settings.SLACK_TOKEN, settings.BOT_NAME)


class IRCThread(threading.Thread):
    __suspend = False

    def __init__(self):
        threading.Thread.__init__(self)
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
                    prefix = text.find('PRIVMSG #%s :' % settings.IRC_CHANNEL)
                    len_prefix = len('PRIVMSG #%s :' % settings.IRC_CHANNEL)
                    if prefix != -1:
                        msg = text[prefix + len_prefix:]
                        for uid in slack.users:
                            msg = msg.replace('<@' + uid + '>', '<@' + slack.users[uid] + '>')
                        username = text[1:text.find('!')]
                        slack.post_message('#' + settings.SLACK_CHANNEL, msg, False, username)
                        print("irc -> slack - " + username + ": " + msg)
            time.sleep(0.01)
        print("IRC Reading Thread Suspended")


class SlackThread(threading.Thread):
    __suspend = False

    def __init__(self):
        threading.Thread.__init__(self)
        print("Slack Reading Thread __init__")

    def suspend(self):
        self.__suspend = True

    def run(self):
        print("Slack Reading Thread run")
        while not self.__suspend:
            raw_text = slack.read()
            if raw_text:
                d = json.loads(raw_text)
                if d.get('type') == 'message' and 'subtype' not in d:
                    if slack.channels.get(d.get('channel')) == settings.SLACK_CHANNEL:
                        userid = d.get('user')
                        username = slack.users.get(userid)
                        if not username:
                            slack.refresh_users()
                            username = slack.users.get(userid) or "?"
                        msg = d.get('text')
                        for uid in slack.users:
                            msg = str.replace(msg, '<@' + uid + '>', '<@' + slack.users[uid] + '>')
                        msg = str.replace(msg, '&lt;', '<').replace('&gt;', '>')
                        irc.send(settings.IRC_CHANNEL, username + ": " + msg)
                        print("slack -> irc - " + username + ": " + msg)
            time.sleep(0.01)
        print("Slack Reading Thread Suspended")


def main():
    irc.init()
    irc.connect(settings.IRC_SERVER, settings.IRC_PORT, settings.IRC_CHANNEL, settings.BOT_NAME)

    print("Clients Loaded")

    irc_thread = IRCThread()
    slack_thread = SlackThread()

    print("Thread Initialized")

    irc_thread.start()
    slack_thread.start()


if __name__ == '__main__':
    main()
