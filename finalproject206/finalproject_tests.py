import unittest
from finalproject import *


class TestDatabase(unittest.TestCase):
    def test_yelp_db(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        statement='SELECT * From yelp '
        statement+='WHERE term="pasta" and location="new york"'
        results=cur.execute(statement)
        result_list=results.fetchall()

        self.assertIn('San Marzano Pasta Fresca', result_list[0][1])
        self.assertEqual(len(result_list), 50)

        statement='SELECT * FROM yelp'
        results=cur.execute(statement)
        result_list=results.fetchall()

        self.assertNotEqual(len(result_list), 0)



    def test_tweet_db(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
        statement='SELECT * FROM tweets '
        statement+='WHERE restaurantname="Chipotle Mexican Grill"'
        results=cur.execute(statement)
        result_list=results.fetchall()
        # print(result_list)

        self.assertEqual('42Stocks', result_list[2][3])
        self.assertEqual(20, result_list[0][5])
        self.assertEqual('tradnews_', result_list[0][3])

        statement='SELECT * FROM tweets '
        results=cur.execute(statement)
        result_list=results.fetchall()

        self.assertNotEqual(len(result_list), 0)

        statement='SELECT * FROM tweets '
        statement+= 'WHERE restaurantname="Whole Foods Market"'
        results=cur.execute(statement)
        result_list=results.fetchall()

        self.assertEqual(result_list[4][3], 'LGrossman02')
        self.assertNotEqual(len(result_list), 0)



class TestInput(unittest.TestCase):
    def test_user_input(self): #need to fully run through code for this to pass
        searchterm='tacos, los angeles'
        searchtermsplit=searchterm.split(", ")
        results=get_data_from_yelp(searchtermsplit[0], searchtermsplit[1])
        self.assertEqual(10, len(results))


class TestDataAccess(unittest.TestCase):
    def test_yelp_cache(self):
        url='https://api.yelp.com/v3/businesses/search'
        term='pasta'
        location='new york'
        params={'term': term, 'location': location, 'limit': 50}
        result1=make_yelp_request_using_cache(url, params)
        results=json.loads(result1)

        self.assertEqual(len(results.values()), 3)
        self.assertEqual(results['businesses'][4]['name'], "Aunt Jake's")
        self.assertIn('businesses', results.keys())

        url='https://api.yelp.com/v3/businesses/search' #
        term='mexican fast food'
        location='ann arbor'
        params={'term': term, 'location': location, 'limit': 50}
        result1=make_yelp_request_using_cache(url, params)
        results=json.loads(result1)
        # print(results)
        self.assertEqual(results['businesses'][0]['name'], 'Isalita')
        self.assertEqual(len(results['businesses']), 44)










unittest.main()
