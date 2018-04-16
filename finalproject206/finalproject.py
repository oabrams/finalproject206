from bs4 import BeautifulSoup
import requests
import json
import secrets
from requests_oauthlib import OAuth1
import certifi
import urllib3
import sqlite3
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
DBNAME = 'yelp_twitter.db'
YELPJSON = 'yelp.json'
TWITTERJSON = 'twitter.json'
API_KEY=secrets.yelp_api_key
HEADERS={'Authorization': 'Bearer {}'.format(API_KEY)}

def init_db():
    try:
        conn=sqlite3.connect(DBNAME)
        cur=conn.cursor()
    except Error in e:
        print(e)
    statement= """
            DROP TABLE IF EXISTS 'yelp';
            """
    cur.execute(statement)
    conn.commit()
    yelp="""
        CREATE TABLE IF NOT EXISTS 'yelp' (
        'Id' Integer primary key AUTOINCREMENT,
        'RestaurantName' TEXT Not Null,
        'City' TEXT,
        'State' TEXT,
        'Address' TEXT,
        'zipcode' Integer,
        'rating' Integer,
        'term' TEXT NOT NULL,
        'location' TEXT NOT NULL)
        """
    cur.execute(yelp)
    conn.commit()


    tweets="""
        CREATE TABLE IF NOT EXISTS 'tweets' (
        'Id' Integer primary key AUTOINCREMENT,
        'RestaurantName' Text,
        'Tweettext' Text,
        'Username' Text,
        'retweets' Integer,
        'favorites' Integer,
        'popularity_score' Integer
        )
        """

    cur.execute(tweets)
    conn.commit()
    statement= """
            DROP TABLE IF EXISTS 'url_link';
            """
    cur.execute(statement)
    conn.commit()

    url_link="""
        CREATE TABLE IF NOT EXISTS 'url_link' (
        'Id' Integer primary key AUTOINCREMENT,
        'Term' TEXT Not Null,
        'Location' Text Not Null)
        """
    cur.execute(url_link)
    conn.commit()

    conn.close()

# try:
#     cache_file=open('cache.json', 'r')
#     cache_contents=cache_file.read()
#     CACHE_DICT=json.loads(cache_contents)
#     cache_file.close()
# except:
#     CACHE_DICT={}

def params_unique_combination(baseurl, params):
    alphabetized_keys=sorted(params.keys())
    res=[]
    for x in alphabetized_keys:
        res.append('{}-{}'.format(x, params[x]))
    return baseurl + '_'.join(res)

#twitter code
try:
    cache_file1=open('twitter_cache.json', 'r')
    cache_contents1=cache_file1.read()
    CACHE_DICT1=json.loads(cache_contents1)
    cache_file1.close()
except:
    CACHE_DICT1={}

def params_unique_combination(baseurl, params):
    alphabetized_keys=sorted(params.keys())
    res=[]
    for x in alphabetized_keys:
        res.append('{}-{}'.format(x, params[x]))
    return baseurl + '_'.join(res)

def make_request_using_cache(url, params={}, auth=None):
    unique_ident=params_unique_combination(url, params)

    if unique_ident in CACHE_DICT1:
        #print('Getting cached data...')
        return CACHE_DICT[unique_ident]
    else:
        #print('Making a request for new data...')
        resp=requests.get(url, params, auth=auth)
        CACHE_DICT1[unique_ident]=resp.text
        dumped_json_cache=json.dumps(CACHE_DICT1)
        fw=open('twitter_cache.json', 'w')
        fw.write(dumped_json_cache)
        fw.close()
        return CACHE_DICT1[unique_ident]

class Tweet:
    def __init__(self, tweet_dict_from_json):

        self.text=tweet_dict_from_json['text']
        self.username=tweet_dict_from_json['user']['screen_name']
        self.creation_date=tweet_dict_from_json['created_at']
        self.num_retweets=tweet_dict_from_json['retweet_count']
        self.num_favorites=tweet_dict_from_json['user']['favourites_count']
        self.popularity_score = (int(self.num_retweets)*2)+(int(self.num_favorites)*3)
        self.id=tweet_dict_from_json['id']
        self.is_retweet = tweet_dict_from_json['retweeted']

    def __str__(self):
        line1= '@{}: {}'.format(self.username, self.text)
        line2='[retweeted {} times]'.format(self.num_retweets)
        line3='[favorited {} times]'.format(self.num_favorites)
        line4='[popularity {}]'.format(self.popularity_score)
        line5='[tweeted on {} | id: {}]'.format(self.creation_date, self.id)
        return line1 + "\n" + line2 + "\n" + line3 + "\n" + line4 + "\n" + line5


def make_request_using_db(url, params, term, location, verify):
    try:
        conn=sqlite3.connect(DBNAME)
        cur=conn.cursor()
    except Error in e:
        print(e)
    insert=(None, term, location)
    statement1='INSERT INTO "url_link" '
    statement1+='Values(?, ?, ?)'
    cur.execute(statement1, insert)
    conn.commit()
    statement= 'SELECT * FROM url_link '
    statement+= 'WHERE term="{}" and location="{}"'.format(term, location)
    x=cur.execute(statement)
    if len(x.fetchall())==1:
        unique_ident=params_unique_combination(url, params)
        resp=requests.request('GET', url, headers=HEADERS, params=params)
        CACHE_DICT[unique_ident]=resp.text
        dumped_json_cache=json.dumps(CACHE_DICT)
        fw=open('cache.json', 'w')
        fw.write(dumped_json_cache)
        yelpinfo=json.loads(CACHE_DICT[unique_ident])


        for x in yelpinfo['businesses']:
            # print(x['name'])
            insert=(None, x['name'], x['location']['city'], x['location']['state'], x['location']['address1'], x['location']['zip_code'], x['rating'], term, location)
            # insert=(None, x[3], x[13]['city'], x[13]['state'], x[13]['address1'], x[13]['zip_code'], x[9])
            statement="INSERT INTO 'yelp' "
            statement+= 'Values (?, ?, ?, ?, ?, ?, ?, ?, ?)'

            cur.execute(statement, insert)
            conn.commit()
        fw.close()
    statement='SELECT * FROM yelp '
    statement+='WHERE term="{}" and location="{}"'.format(term, location)
    b=cur.execute(statement)
    if len(b.fetchall())==0:
        print('No information found with your search information. Try again.')
        return('No information found with your search information. Try again.')
        # return CACHE_DICT[unique_ident]
    newinput=input('Enter "alpha" for a list of 10 restaurants sorted alphabetically or enter "top" for a list of the top 10 rated restaurants according to your query: ')
    if newinput=="alpha":
        statement='SELECT RestaurantName, rating '
        statement+='FROM yelp WHERE term="{}" and location="{}" '.format(term, location)
        statement+='ORDER By RestaurantName LIMIT 10'
        cur.execute(statement)
        count= 1
        for x in cur:
            print(count, x[0], 'Rating:', x[1])
            count+=1
        #PLOTLY !!!
        number_next_input=input('Enter a number that corresponds with a restaurant from the list for more information or enter "next" and receive a list of the next 10 restaurants from the database: ')
        if number_next_input=='next':
            statement='SELECT RestaurantName, rating '
            statement+='FROM yelp WHERE term="{}" and location="{}" '.format(term, location)
            statement+='ORDER BY RestaurantName LIMIT 20'
            nextinfo=cur.execute(statement)
            countagain=11
            list1=[]
            for x in nextinfo:
                list1.append(x)
            updatedlist=list1[10:]
            for x in updatedlist:
                print(countagain, x[0], 'Rating:', x[1])
                countagain+=1
            finalinput=input('Enter a number that corresponds with a restaurant from the list for more information or enter "new query" to search a new term and location: ')
            if finalinput.isdigit() and int(finalinput)<= 20:
                statement='SELECT RestaurantName, rating, Address, City, State, zipcode '
                statement+='FROM yelp WHERE term="{}" and location="{}" '.format(term, location)
                statement+='ORDER BY RestaurantName LIMIT 20'
                nextinfo=cur.execute(statement)
                list1=[]
                for x in nextinfo:
                    list1.append(x)
                print(list1[int(finalinput)-1][0],'\n', 'Rating:', list1[int(finalinput)-1][1], '\n', list1[int(finalinput)-1][2], list1[int(finalinput)-1][3], list1[int(finalinput)-1][4])
                tweetinput=input('Enter "tweets" for a list of tweets about the selected restaurant or "exit" to leave the programs: ')
                if tweetinput=='tweets':
                    get_tweets_for_restaurant(list1[int(finalinput)-1][0])

        #ask another user input about whether you want to select a restaurant or enter another query
        elif number_next_input.isdigit() and int(number_next_input)<= 10:
            statement='SELECT RestaurantName, rating, Address, City, State, zipcode '
            statement+='FROM yelp WHERE term="{}" and location="{}" '.format(term, location)
            statement+='Order by RestaurantName LIMIT 10'
            moreinfo=cur.execute(statement)
            listagain=[]
            for x in moreinfo:
                listagain.append(x)
            print(listagain[int(number_next_input)-1][0], '\n', 'Rating:', listagain[int(number_next_input)-1][1], '\n', listagain[int(number_next_input)-1][2], listagain[int(number_next_input)-1][3], listagain[int(number_next_input)-1][4], listagain[int(number_next_input)-1][5])
            tweetinput=input('Enter "tweets" for a list of tweets about the selected restaurant or "exit" to leave the programs: ')
            if tweetinput=='tweets':
                get_tweets_for_restaurant(listagain[int(number_next_input)-1][0])



    elif newinput=='top':
        statement='SELECT RestaurantName, rating '
        statement+='FROM yelp WHERE term="{}" and location="{}" '.format(term, location)
        statement+='Order By rating Desc Limit 10'
        cur.execute(statement)
        count=1
        for x in cur:
            print(count, x[0], 'Rating:', x[1])
            count+=1
        #PLOTLY !!!
        number_next_input=input('Enter a number that corresponds with a restaurant from the list for more information or enter "next" and receive a list of the next 10 restaurants from the database: ')
        if number_next_input=='next':
            statement='SELECT RestaurantName, rating '
            statement+='FROM yelp WHERE term="{}" and location="{}" '.format(term, location)
            statement+='Order By rating Desc Limit 20'
            nextinfo=cur.execute(statement)
            countagain=11
            list1=[]
            for x in nextinfo:
                list1.append(x)
            updatedlist=list1[10:]
            for x in updatedlist:
                print(countagain, x[0], 'Rating:', x[1])
                countagain+=1
            finalinput=input('Enter a number that corresponds with a restaurant from the list for more information or enter "new query" to search a new term and location: ')
            if finalinput.isdigit() and int(finalinput)<= 20:
                statement='SELECT RestaurantName, rating, Address, City, State, zipcode '
                statement+='FROM yelp WHERE term="{}" and location="{}" '.format(term, location)
                statement+='ORDER BY rating Desc Limit 20'
                nextinfo=cur.execute(statement)
                list1=[]
                for x in nextinfo:
                    list1.append(x)
                print(list1[int(finalinput)-1][0], '\n', 'Rating:', list1[int(finalinput)-1][1], '\n', list1[int(finalinput)-1][2], list1[int(finalinput)-1][3], list1[int(finalinput)-1][4])
                tweetinput=input('Enter "tweets" for a list of tweets about the selected restaurant or "exit" to leave the programs: ')
                if tweetinput=='tweets':
                    get_tweets_for_restaurant(list1[int(finalinput)-1][0])
        #ask another user input about whether you want to select a restaurant or enter another query
        elif number_next_input.isdigit() and int(number_next_input)<= 10:
            statement='SELECT RestaurantName, rating, Address, City, State, zipcode '
            statement+='FROM yelp WHERE term="{}" and location="{}" '.format(term, location)
            statement+='Order by rating DESC Limit 10'
            moreinfo=cur.execute(statement)
            listagain=[]
            for x in moreinfo:
                listagain.append(x)
            print(listagain[int(number_next_input)-1][0], '\n', 'Rating:', listagain[int(number_next_input)-1][1], '\n', listagain[int(number_next_input)-1][2], listagain[int(number_next_input)-1][3], listagain[int(number_next_input)-1][4], listagain[int(number_next_input)-1][5])
            tweetinput=input('Enter "tweets" for a list of tweets about the selected restaurant or "exit" to leave the programs: ')
            if tweetinput=='tweets':
                get_tweets_for_restaurant(listagain[int(number_next_input)-1][0])
    else:
        print('Invalid input')

def get_data_from_yelp(term, location):
    url='https://api.yelp.com/v3/businesses/search'
    params={'term': term, 'location': location, 'limit': 50}
    response=make_request_using_db(url, params=params, term=term, location=location, verify=False)
    conn=sqlite3.connect(DBNAME)
    cur=conn.cursor()
    conn.close()

def get_tweets_for_restaurant(restaurant):
    twitter_key=secrets.twitter_client_key
    twitter_secret=secrets.twitter_client_secret
    access_token=secrets.twitter_access_token
    access_secret=secrets.twitter_access_token_secret

    baseurl='https://api.twitter.com/1.1/search/tweets.json'
    params={'q': restaurant, 'count': 100}
    auth=OAuth1(twitter_key, twitter_secret, access_token, access_secret)
    response=make_request_using_cache(baseurl, params=params, auth=auth)
    tweetdict=json.loads(response)


    tweet_list=[]
    tweetinfo=tweetdict['statuses']
    for item in range(len(tweetinfo)):
        tweetmore=tweetinfo[item]
        tweet_list.append(Tweet(tweetmore))
    updatedtweetlist=[]
    for x in tweet_list:
        if x.is_retweet==False:
            updatedtweetlist.append(x)
            # print(type(x.popularity_score))
    finallist=sorted(updatedtweetlist, key=lambda x: x.popularity_score, reverse=True)[:10]
    if len(finallist)!=0:
        for x in finallist:
            print(x)
            print('-'*20)
        return finallist
    else:
        print('No tweets found about {}'.format(restaurant))

def interactive_prompt():
    response = ''
    help_text= 'Enter any term related to food. This can include a type of cuisine, a type of food, or a specific meal. \n Examples: \nTacos, Encino\n Breakfast, New York\n Italian, Ann Arbor'
    while response != 'exit':
        response = input('Enter a term and location separated by a comma or enter "help" for more information: ')
        if response == 'help':
            print(help_text)
            continue
        elif "," in response:
            searchterm=response.split(', ')
            get_data_from_yelp(searchterm[0], searchterm[1])
        elif response=='exit':
            break
        else:
            print('Invalid input, try again.')
# init_db()
# get_data_from_yelp('Breakfast', '91436')
interactive_prompt()
# restaurantjsoninfo()
