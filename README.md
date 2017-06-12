# slack-irc-echobot

IRC에서 Slack으로, Slack에서 IRC로 그대로 전달해주는 봇

### Setting

`settings.default.py` 파일을 `settings.py`로 복사 후 수정

- BOT_NAME : 봇의 닉네임
- IRC_SERVER : IRC 서버의 주소
- IRC_PORT : IRC 서버의 포트
- IRC_CHANNEL : IRC 서버의 채널 (# 없이)
- SLACK_TOKEN : Slack Bot 토큰
- SLACK_CHANNEL : Slack 서버의 채널 (# 없이)

### Usage in IRC and Slack

IRC와 Slack 안에서의 명령어

```
# 현재 채널을 echo할 채널로 설정
?setechohere
# 다음 닉네임들이 하는 말은 무시
?setignore <nick1> <nick2> ...
# 다음 닉네임을 더이상 무시하지 않음
?unsetignore <nick1> <nick2> ...
```

### Requirements

- requests
- slacker
- websocket-client

--------

[GNU AGPL 3.0 License](LICENSE.md)

[pbzweihander](https://github.com/pbzweihander)
