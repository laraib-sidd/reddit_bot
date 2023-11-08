import pytz
from datetime import datetime as dt
import urllib.request
import config
import pymongo
import json
import praw

# Firebase


def get_reddit_client():
    reddit = praw.Reddit(
        client_id=config.reddit["client_id"],
        client_secret=config.reddit["client_secret"],
        user_agent=config.reddit["user_agent"],
        # username=config.reddit["username"],
        # password=config.reddit["password"]
    )
    return reddit


def create_mongo_client():
    mongo_user = config.mongo["user"]
    mongo_pass = config.mongo["password"]
    mongo_uri = config.mongo["uri"]
    mongo_db = config.mongo["db_name"]
    srv = f"mongodb+srv://{mongo_user}:{mongo_pass}@{mongo_uri}/?retryWrites=true&w=majority"
    client = pymongo.MongoClient(srv)
    return client[mongo_db]


def insert_mongo_collection(id, collection):
    collection.insert_one({"id": id})
    return None


def check_post_id_mongo(id, collection):
    id_count = collection.count_documents({"id": id})
    if id_count:
        return True
    else:
        return False


def delete_old_ids(collection):
    cols_count = collection.count_documents({})
    if cols_count > 100:
        collection.delete_many({})
    return None


def get_start_end_timestamp():
    now_time = dt.today()
    end_time = now_time.timestamp()
    start_time = end_time - 300
    return int(start_time), int(end_time)


def calculate_time_difference(utc_timestamp):
    utc_tz = pytz.utc
    utc_dt = dt.utcfromtimestamp(utc_timestamp).replace(tzinfo=utc_tz)
    ist_tz = pytz.timezone("Asia/Kolkata")
    ist_dt = utc_dt.astimezone(ist_tz)
    now_dt = dt.now(ist_tz)
    total_seconds_passed = (now_dt - ist_dt).total_seconds()
    minutes_passed = total_seconds_passed / 60

    if minutes_passed >= 60:
        hours_passed = minutes_passed / 60
        return f"{hours_passed:.2f} hours have passed this post was created {ist_dt:%Y/%m/%d-%H:%M}"
    else:
        return f"{minutes_passed:.2f} minutes have passed this post was created {ist_dt:%Y/%m/%d-%H:%M}" 


def get_filtered_posts_with_praw(sub_name, reddit_client,mongo_client):
    subreddit_client = reddit_client.subreddit(sub_name)
    mongo_collection = mongo_client[sub_name]
    filtered_posts = []
    for post in subreddit_client.new(limit=20):
        if (post.link_flair_text == "Hiring" or post.link_flair_text == "Hiring - Open" or post.link_flair_text == "Task"):
            post_dict = {}
            post_dict["id"] = post.id
            id_exist = check_post_id_mongo(post_dict["id"], mongo_collection)
            if id_exist:
                continue
            else:
                posted_ago = calculate_time_difference(post.created_utc)
                
                post_dict["posted_ago"] = posted_ago
                post_dict["title"] = post.title
                post_dict["url"] = post.url
                post_dict["selftext"] = post.selftext
                post_dict["subreddit"] = sub_name

                # insert_mongo_collection(post_dict["id"], mongo_collection)
                filtered_posts.append(post_dict)
        else:
            continue
    return filtered_posts


def get_all_posts():
    reddit_client = get_reddit_client()
    mongo_client = create_mongo_client()
    filtered_posts = []
    filtered_posts.append(get_filtered_posts_with_praw("forhire",reddit_client,mongo_client))
    filtered_posts.append(get_filtered_posts_with_praw("slavelabour",reddit_client,mongo_client))
    filtered_posts.append(get_filtered_posts_with_praw("Jobs4Bitcoins",reddit_client,mongo_client))

    return filtered_posts


if __name__ == "__main__":
    s = get_all_posts()
    print(s)
    # reddit = get_reddit_client()
    # # st_time, end_tim = get_start_end_timestamp()
    # forhire = reddit.subreddit('Jobs4Bitcoins')
    # for post in forhire.new(limit=20):
    #     print(post.url)
    #     print(post.link_flair_text)
