import os
import json
import pprint
import copy
import collections
from requests_oauthlib import OAuth1Session

# MOVE THESE TO A MORE SECURE METHOD

consumer_key = open("api_key.txt", "r").readline()  # API key
consumer_secret = open("api_secret_key.txt", "r").readline()  # API secret key


class ItemCount:
    def __init__(self, name, count):
        self.name = name
        self.count = count

    name = ""
    count = 0


def sort_func(e):
    return e.count


def check_if_in_list(item, item_list):
    for i in item_list:
        if i == item:
            return True
    return False


def count_items(item_list):
    counter_list = []
    for i in item_list:
        found = False
        for j in counter_list:
            if i == j.name:
                j.count += 1
                found = True
                break
        if not found:
            counter_list.append(ItemCount(i, 1))
    return counter_list


def combine_occurrences(list1, list2):
    combined_list = copy.deepcopy(list1)
    for i in list2:
        found = False
        for j in range(len(list1)):
            if i.name == list1[j].name:
                combined_list[j].count += i.count
                found = True
                break
        if not found:
            combined_list.append(ItemCount(i.name, i.count))
    return combined_list


def get_oauth_session():
    # Get request token
    request_token_url = "https://api.twitter.com/oauth/request_token"
    oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)
    fetch_response = oauth.fetch_request_token(request_token_url)
    resource_owner_key = fetch_response.get('oauth_token')
    resource_owner_secret = fetch_response.get('oauth_token_secret')
    print("Got OAuth token: %s" % resource_owner_key)

    # # Get authorization
    base_authorization_url = 'https://api.twitter.com/oauth/authorize'
    authorization_url = oauth.authorization_url(base_authorization_url)
    print('Please go here and authorize: %s' % authorization_url)
    verifier = input('Paste the PIN here: ')

    # # Get the access token
    access_token_url = 'https://api.twitter.com/oauth/access_token'
    oauth = OAuth1Session(consumer_key,
                          client_secret=consumer_secret,
                          resource_owner_key=resource_owner_key,
                          resource_owner_secret=resource_owner_secret,
                          verifier=verifier)
    oauth_tokens = oauth.fetch_access_token(access_token_url)

    access_token = oauth_tokens['oauth_token']
    access_token_secret = oauth_tokens['oauth_token_secret']

    # Make the request
    oauth = OAuth1Session(consumer_key,
                          client_secret=consumer_secret,
                          resource_owner_key=access_token,
                          resource_owner_secret=access_token_secret)
    return oauth


def get_tweet(oauth, max_id=-1):

    if max_id == -1:
        params = {"count": "200"}
    else:
        params = {"count": "200", "max_id": max_id}

    response = oauth.get("https://api.twitter.com/1.1/statuses/home_timeline.json", params=params)
    parsed_response = json.loads(response.text)

    # Create list of names
    name_list = []
    oldest_id = parsed_response[0]["id"]
    for i in parsed_response:
        name_list.append(i["user"]["name"])
        if i["id"] < oldest_id:
            oldest_id = i["id"]
        # pprint.pprint("%s: %s" % (i["user"]["name"], i["text"].replace('\n', "  ")))

    # Count occurrences of names
    occurrences = count_items(name_list)
    occurrences.sort(reverse=True, key=sort_func)
    total_tweets = 0
    for i in occurrences:
        total_tweets += i.count

    print("Tweets in this pass: %d" % total_tweets)
    # print(occurrences, "\n")

    # for i in occurrences:
    #     print("%s: %s %%" % (i.name, round(i.count / total_tweets * 100, 1)))
    return oldest_id, occurrences


if __name__ == '__main__':
    oauth = get_oauth_session()
    total_occurrences = []
    oldest_id = -1

    for i in range(5):
        oldest_id, partial_occurrences = get_tweet(oauth=oauth, max_id=oldest_id)
        total_occurrences = combine_occurrences(total_occurrences, partial_occurrences)

    total_occurrences.sort(reverse=True, key=sort_func)

    # Print results
    print("\nTotal Results:")
    total_tweets = 0
    for i in total_occurrences:
        total_tweets += i.count

    print("Tweets analyzed: %d" % total_tweets)
    # print(occurrences, "\n")

    for i in total_occurrences:
        print("%s: %s %%" % (i.name, round(i.count / total_tweets * 100, 1)))