# coding: utf-8
import tweepy
import pandas as pd
import requests
import pickle

#APIkey
auth = tweepy.OAuthHandler("CONSUMER_KEY", "CONSUMER_SECRET")
auth.set_access_token("ACCESS_TOKEN", "ACCESS_TOKEN_SECRET")
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

#対象のアカウントを指定
fetch_target_tweets = api.user_timeline(screen_name = "USER_NAME",tweet_mode='extended')

#保存先のディレクトリ
path = "PATH"

#これまでに保存したtweetに関するtweet_idのリストがあれば取得する
try:
    with open(path+"ids","rb")as idreader:
        past_ids = pickle.load(idreader)
except FileNotFoundError:
    past_ids = []

ids = []
screen_names = []
user_names = []
tweet_times = []
texts = []
media_urls = []
past_ids_set = set(past_ids)

#ツイート情報とURLの取得
for tweet in fetch_target_tweets:
    #過去に取得したツイートは除外
    if tweet.id in past_ids_set:
        pass
    #RT以外のツイートは除外
    elif "RT @" not in tweet.full_text:
        pass
    elif "RT @" in tweet.full_text:
        #ツイートid、スクリーンネーム、ユーザ名、ツイート日時をリストに保存
        ids.append(tweet.id)
        screen_names.append(tweet.retweeted_status.user.screen_name)
        user_names.append(tweet.retweeted_status.user.name)
        tweet_times.append(tweet.retweeted_status.created_at)

        #メディア付きツイートでなければ本文を保存　media_urlsには空白を保存
        try:
            a = tweet.retweeted_status.extended_entities
        except AttributeError as e:
            #print(tweet.retweeted_status.full_text)
            texts.append(tweet.retweeted_status.full_text)
            media_urls.append("")

        #メディア付きツイートなら本文を保存
        else:
            #print(tweet.retweeted_status.full_text)
            texts.append(tweet.retweeted_status.full_text)

            #動画付きツイートなら動画のURLを取得　最もbitrateが高いものにする
            if "video_info" in tweet.retweeted_status.extended_entities["media"][0]:
                dicts = [i for i in tweet.retweeted_status.extended_entities["media"][0]["video_info"]["variants"] if "bitrate" in i]
                dicts_2 = [i["bitrate"] for i in dicts]
                media_urls.append(dicts[dicts_2.index(max(dicts_2))]["url"])
                #print(dicts[dicts_2.index(max(dicts_2))]["url"])

            #画像つきツイートなら画像のURLを保存　オリジナル画質にする
            elif "video_info" not in tweet.retweeted_status.extended_entities:
                murl = []
                for i in range(len(tweet.retweeted_status.extended_entities["media"])):
                    murl.append(tweet.retweeted_status.extended_entities["media"][i]["media_url"] + ":orig")
                    #print(tweet.retweeted_status.extended_entities["media"][0]["media_url"] + ":orig")
                media_urls.append(murl)


#URLから画像・動画を保存、ファイル名をリストに保存
filenames = []
for i in media_urls:
    #print(i)

    #画像URLのリストからURLを取り出してダウンロード
    if type(i) == list:
        #print("list")
        fns = []
        for j in range(len(i)):
            #print(i[j])
            filename = i[j].split('/')[-1]
            filename = filename[:-5]
            fns.append(filename)
            response = requests.get(i[j])
            savepath = path + filename
            image = response.content
            with open(savepath, "wb") as aaa:
                aaa.write(image)
        filenames.append(fns)

    #動画URLからダウンロード
    elif type(i) == str:
        #print("str")
        if "orig" in i:
            filename = i.split('/')[-1]
            filename = filename[:-5]
            filenames.append(filename)
            response = requests.get(i)
            savepath = path + filename
            image = response.content
            with open(savepath, "wb") as aaa:
                aaa.write(image)
        elif "?" in i:
            filename = i.split('/')[-1]
            filename = filename[0:filename.find("?")]
            filenames.append(filename)
            response = requests.get(i)
            savepath = path + filename
            image = response.content
            with open(savepath, "wb") as aaa:
                aaa.write(image)
        #urlが''なら何もしない
        elif i == "":
            #print(i)
            filenames.append("")


#ツイートについての情報をdfにして保存
if ids != []:
    past_ids.extend(ids)
    with open(path+"ids","wb")as idwriter:
        pickle.dump(past_ids,idwriter)

    #以前のdfがあればそれと結合
    try:
        with open(path+"df","rb")as dfreader:
            df1 = pickle.load(dfreader)
        zips = zip(ids,screen_names,user_names,tweet_times,texts,filenames)
        df2 = pd.DataFrame([i for i in zips], columns=["id","screen_name","user_name","tweet_time","text","filename"])
        df3 = pd.concat([df1,df2])
        with open(path+"df","wb")as dfwriter:
            pickle.dump(df3,dfwriter)

    #以前のdfがなければ新たに作成
    except FileNotFoundError:
        zips = zip(ids,screen_names,user_names,tweet_times,texts,filenames)
        df2 = pd.DataFrame([i for i in zips], columns=["id","screen_name","user_name","tweet_time","text","filename"])
        with open(path+"df","wb")as dfwriter:
            pickle.dump(df2,dfwriter)
