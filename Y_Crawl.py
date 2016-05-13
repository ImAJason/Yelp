
# coding: utf-8

from bs4 import BeautifulSoup
import urllib
import re
import pandas as pd
import numpy as np
import time

URL = lambda zipcode, page_num: 'http://www.yelp.com/search?find_loc={0}&start={1}&cflt=food'.format(zipcode, page_num)


def individual_restaurants(zipcode, page_num):
    url = URL(zipcode, page_num)
    r = urllib.urlopen(url).read()
    soup = BeautifulSoup(r)
    restaurant_list = []
    restaurants = soup.findAll('span', {'class':'indexed-biz-name'})
    #restaurants = soup.findAll('li', attrs={'class':re.compile
        #(r'regular-search-result')})
    for r in restaurants:
        individual_url = r.find('a', {'class':'biz-name'}).get('href')
        individual_url = 'http://www.yelp.com'+individual_url+'?start=0'
        restaurant_list.append(individual_url)
    return restaurant_list, True
#individual_restaurants(77494, 0)

def list_of_restaurants(zipcode):
    page_num = 0
    flag = True

    if zipcode is None:
        print 'No Zipcode'

    all_restaurants = []
    
    while page_num < 10:
    #while flag:
        restaurant_list, flag = individual_restaurants(zipcode, page_num)
        all_restaurants.extend(res for res in restaurant_list)
        #if not flag:
            #break
        page_num += 10
        time.sleep(np.random.randint(1, 2) * .9123456)

    return all_restaurants
#list_of_restaurants(77494)

def businesses():
    restaurant_list = list_of_restaurants(zipcode)
    
    #list names
    user_ID_list = []
    business_ID_list = []
    biz_name_list = []
    business_avg_list = []
    business_review_count_list = []
    review_id_list = []
    stars_list = []
    
    for res in restaurant_list:
        
        r = urllib.urlopen(res).read()
        soup = BeautifulSoup(r)
                
        
        #business_ID
        business_ID = soup.find('a', attrs={'class':re.compile
            (r'biz-name')}).get('data-hovercard-id')

        #biz_name
        biz_name = soup.find('a', {'class':'biz-name'}).getText()

        #business_avg
        business_avg = soup.find('i', {'class':re.compile(r'star-img\w*')}).get('title')
        business_avg = float(business_avg[0:3])

        #business_review_count
        business_review_count = soup.find('span', {'class':'review-count rating-qualifier'}).getText()
        business_review_count = int(business_review_count[0:business_review_count.index(' ')])
        
        #user_ID & review_ID
        find_review_ID = soup.findAll('div', {'class': 'review review--with-sidebar'})
        for r in find_review_ID:

            #user_ID
            user_ID = r.get('data-signup-object')
            user_ID = user_ID[8:]

            #review_ID
            review_ID = r.get('data-review-id')

            #stars
            stars = r.find('i', {'class':re.compile(r'star-img\w*')}).get('title')
            stars = float(stars[0:3])

            #fill the lists
            user_ID_list.append(user_ID)
            business_ID_list.append(business_ID)
            biz_name_list.append(biz_name)
            business_avg_list.append(business_avg)
            business_review_count_list.append(business_review_count)
            review_id_list.append(review_ID)
            stars_list.append(stars)
            
        time.sleep(np.random.randint(1, 2))

    #pandas stuffs
    df=pd.DataFrame(user_ID_list,columns=['user_ID'])
    df['business_ID'] = business_ID_list
    df['biz_name'] = biz_name_list
    df['business_avg'] = business_avg_list
    df['business_review_count'] = business_review_count_list
    df['review_id'] = review_id_list
    df['stars'] = stars_list
    return df

def individual_urls(zipcode):
    restaurant_list = list_of_restaurants(zipcode)
    individual_urls = []
    for res in restaurant_list:
        r = urllib.urlopen(res).read()
        soup = BeautifulSoup(r)
        all_user_link = soup.findAll('div', {'class': 'review review--with-sidebar'})
        for a in all_user_link:
            user_link = a.find('a', {'class':re.compile(r'user-display-name')}).get('href')
            user_link = 'http://www.yelp.com' + user_link
            individual_urls.append(user_link)
    return individual_urls
#individual_urls()

def individual(zipcode):
    user_list = individual_urls(zipcode)
    
    #lists
    user_review_count_list = []
    user_avg_list = []
    user_ID_list = []
    
    #u = user_list[2]
    for u in user_list:
        r = urllib.urlopen(u).read()
        soup = BeautifulSoup(r)

        #user_review_count
        user_review_count = int(soup.find('li', {'class':'review-count'}).strong.getText())

        #user_avg
        calculate = soup.findAll('td',{'class':'histogram_count'})
        avg_calc = []
        for c in calculate:
            rating_totals = int(c.getText())
            avg_calc.append(rating_totals)
        five_ratings = avg_calc[0] * 5
        four_ratings = avg_calc[1] * 4
        three_ratings = avg_calc[2] * 3
        two_ratings = avg_calc[3] * 2
        one_ratings = avg_calc[4] * 1
        sum_of_ratings = five_ratings + four_ratings + three_ratings + two_ratings + one_ratings
        user_avg = float(sum_of_ratings / user_review_count)

        #fill the lists
        user_review_count_list.append(user_review_count)
        user_avg_list.append(user_avg)
        user_ID_list.append(u[-22:])

    df=businesses()
    df2=pd.DataFrame(user_review_count_list,columns=['user_review_count'])
    df2['user_avg'] = user_avg_list
    df2['user_ID'] = user_ID_list
    merged_df = pd.merge(df,df2, on='user_ID')
    return merged_df
#individual()

#zipcode = 77494
merged_df = individual(zipcode)
merged_df.to_csv('/Users/jasonwang/Desktop/YelpExtract.csv', sep='\t')
