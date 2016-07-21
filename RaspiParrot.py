#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import twitter
import time
import logging
import configparser

CONFIGFILE="config.ini"
inifile=None

def init():
    global inifile
    inifile = configparser.ConfigParser()
    inifile.read(CONFIGFILE)

    global logger
    logging.basicConfig(filename=inifile.get("log","filename"),
                        level=logging.INFO,
                        format='%(asctime)-15s %(levelname)s %(message)s')
    logger = logging.getLogger("RaspiParrot")

def GetAPI():
    global inifile
    logger.info("Twitter APIの使用を開始します。")
    consumer_key    = inifile.get("keys", "TWEETUSERNAME")
    consumer_secret = inifile.get("keys", "TWEETPASSWORD")
    access_key      = inifile.get("keys", "TWEETACCESSKEY")
    access_secret   = inifile.get("keys", "TWEETACCESSSECRET")
    encoding        = 'utf-8'
    return twitter.Api(consumer_key=consumer_key,
                       consumer_secret=consumer_secret,
                       access_token_key=access_key,
                       access_token_secret=access_secret,
                       input_encoding=encoding)

def OneCycle():
    global inifile
    logger.info(u"----- OneCycle開始 -----")
    LastMentionSeconds = int(inifile.get("records", "LastMentionSeconds"))

    # Twitter APIを使える状態にする。有効時間60秒らしい。
    api = GetAPI()

    # 自分自身に届いたMentionを確認する。最大20個らしい。
    try:
        MaxMentionSeconds = 0
        for state in api.GetMentions():
            logging.debug(u"LastMentionSeconds:%s" % ( LastMentionSeconds ))
            logging.debug(u"created_at_in_seconds:%s" % ( state.created_at_in_seconds ))
            t = time.strftime(u"%Y-%m-%d %H:%M:%S", time.localtime(state.created_at_in_seconds))
            if LastMentionSeconds < state.created_at_in_seconds:
                 logger.info(u"新しいMentionが到着:[%s] %s" % (t, state.user.screen_name) )
                 # このMentionは未処理なので応答を返す
                 ReplyMention(api, state)
                 if MaxMentionSeconds < state.created_at_in_seconds:
                     MaxMentionSeconds = state.created_at_in_seconds
            else:
                 logger.info(u"返答済みのMention:[%s] %s" % (t, state.user.screen_name) )
        # メンション応答があった場合はLastMentionSecondsを更新
        if MaxMentionSeconds != 0:
            inifile.set("records", "LastMentionSeconds", str(MaxMentionSeconds))
            inifile.write(open(CONFIGFILE, 'w'))
    except UnicodeDecodeError:
        print("Your message could not be encoded.  Perhaps it contains non-ASCII characters? ")
        print("Try explicitly specifying the encoding with the --encoding flag")
        sys.exit(2)
    logger.info(u"----- OneCycle終了 -----")
    
def ReplyMention(api, state):
    # Mentionが届いている。何か気の利いた返答をしよう。
    logger.info(u"Mention返しを開始")
    t = time.strftime(u"%Y-%m-%d %H:%M:%S", time.localtime())
    message = u"@%s メンションありがとう[%s]" % ( state.user.screen_name, t )
    newstates = api.PostUpdate(message, in_reply_to_status_id=state.id)

def main():
    init()
    while True:
        OneCycle()
        # Twitter API Rate Limitにより、15回/15分の制限がある
        time.sleep(180)

if __name__ == "__main__":
    main()
