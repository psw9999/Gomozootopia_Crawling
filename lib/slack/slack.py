import requests

class SlackBot:
    token = "none"
    channel = "#test"

    def __init__(self, token):
        self.token = token

    def slack_post_message(self, channel, msg):
        self.channel = channel
        requests.post("https://slack.com/api/chat.postMessage",
            headers={"Authorization": "Bearer "+self.token},
            data={"channel": self.channel, "text": msg})


if __name__ == "__main__":
    print("SlackBot Test Main")
    sl = SlackBot("xoxb-3040674388865-3013432400759-NKjLH4nlL1CzMwDil9SYUpvh")
    sl.slack_post_message('#crawling', 'test')
