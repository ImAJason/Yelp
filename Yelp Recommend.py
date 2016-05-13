
# coding: utf-8

# In[1]:

get_ipython().magic(u'matplotlib inline')
from collections import defaultdict
import json
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import pandas as pd


# In[2]:

df=pd.read_csv("bigdf.csv")


# In[3]:

def recalculate(odf):
    
    #Recalculates averages/review counts based on new subset.

    odfu=odf.groupby('user_id')
    odfb=odf.groupby('business_id')
    user_avg=odfu.stars.mean()
    user_review_count=odfu.review_id.count()
    business_avg=odfb.stars.mean()
    business_review_count=odfb.review_id.count()
    ndf=odf.copy()
    ndf.set_index(['business_id'], inplace=True)
    ndf['business_avg']=business_avg
    ndf['business_review_count']=business_review_count
    ndf.reset_index(inplace=True)
    ndf.set_index(['user_id'], inplace=True)
    ndf['user_avg']=user_avg
    ndf['user_review_count']=user_review_count
    ndf.reset_index(inplace=True)
    return ndf


# In[6]:

# Make a smaller data set based on specified numbers
Filtered = df[(df.user_review_count>65) & (df.business_review_count>155)]
fdf= recalculate(Filtered)


# In[7]:

from scipy.stats.stats import pearsonr
def pearson_sim(rest1_reviews, rest2_reviews, n_common):
    if n_common==0:
        rho=0.
    else:
        diff1=rest1_reviews['stars']-rest1_reviews['user_avg']
        diff2=rest2_reviews['stars']-rest2_reviews['user_avg']
        rho=pearsonr(diff1, diff2)[0]
    return rho


# In[8]:

def get_restaurant_reviews(restaurant_id, df, set_of_users):
    """
    given a resturant id and a set of reviewers, return the sub-dataframe of their
    reviews.
    """
    Set = (df.user_id.isin(set_of_users)) & (df.business_id==restaurant_id)
    reviews = df[Set]
    reviews = reviews[reviews.user_id.duplicated()==False]
    #reviews = reviews[reviews.drop_duplicates(reviews.user_id)]
    return reviews


# In[9]:

def calculate_similarity(rest1, rest2, df, similarity_func):
    
    # find common reviewers
    
    rest1_reviewers = df[df.business_id==rest1].user_id.unique()
    rest2_reviewers = df[df.business_id==rest2].user_id.unique()
    common_reviewers = set(rest1_reviewers).intersection(rest2_reviewers)
    n_common=len(common_reviewers)
    
    #get reviews
    
    rest1_reviews = get_restaurant_reviews(rest1, df, common_reviewers)
    rest2_reviews = get_restaurant_reviews(rest2, df, common_reviewers)
    sim=similarity_func(rest1_reviews, rest2_reviews, n_common)
    if np.isnan(sim):
        return 0, n_common
    return sim, n_common


# In[10]:

class Database:
    "A class representing a database of similaries and common supports"
    
    def __init__(self, df):
        "the constructor, takes a reviews dataframe like smalldf as its argument"
        database={}
        self.df=df
        self.uniquebizids={v:k for (k,v) in enumerate(df.business_id.unique())}
        keys=self.uniquebizids.keys()
        l_keys=len(keys)
        self.database_sim=np.zeros([l_keys,l_keys])
        self.database_sup=np.zeros([l_keys, l_keys], dtype=np.int)
        
    def populate_by_calculating(self, similarity_func):
        """
        a populator for every pair of businesses in df. takes similarity_func like
        pearson_sim as argument
        """
        items=self.uniquebizids.items()
        for b1, i1 in items:
            for b2, i2 in items:
                if i1 < i2:
                    sim, nsup=calculate_similarity(b1, b2, self.df, similarity_func)
                    self.database_sim[i1][i2]=sim
                    self.database_sim[i2][i1]=sim
                    self.database_sup[i1][i2]=nsup
                    self.database_sup[i2][i1]=nsup
                elif i1==i2:
                    nsup=self.df[self.df.business_id==b1].user_id.count()
                    self.database_sim[i1][i1]=1.
                    self.database_sup[i1][i1]=nsup
                    

    def get(self, b1, b2):
        "returns a tuple of similarity,common_support given two business ids"
        sim=self.database_sim[self.uniquebizids[b1]][self.uniquebizids[b2]]
        nsup=self.database_sup[self.uniquebizids[b1]][self.uniquebizids[b2]]
        return (sim, nsup)


# In[11]:

db=Database(fdf)
db.populate_by_calculating(pearson_sim)


# In[12]:

def shrunk_sim(sim, n_common):
    "takes a similarity and shrinks it down by using the regularizer"
    nsim=(n_common*sim)/(n_common+3.)
    return nsim


# In[45]:

from operator import itemgetter
def knearest(restaurant_id, set_of_restaurants, dbase, k=5.):
    """
    Given a restaurant_id, dataframe, and database, get a sorted list of the
    k most similar restaurants from the entire database.
    """
    sorted_similar = []
    for s in set_of_restaurants:
        if s != restaurant_id:
            sim,nc = dbase.get(restaurant_id, s)
            shrunk = shrunk_sim(sim,nc)
            sorted_similar.append((s, shrunk, nc))
    sorted_similar=sorted(sorted_similar, key=itemgetter(1), reverse = True)
    return sorted_similar[0:k]


# In[46]:

testbizid="eIxSLxzIlfExI6vgAbn2JA"


# In[53]:

def businessname(df, tid):
    return df['biz_name'][df['business_id']==tid].values[0]
def idname(df, tid):
    return df['user_name'][df['user_id']==tid].values[0]


# In[66]:

tops=knearest(testbizid, fdf.business_id.unique(), db, k=5)
print "For",businessname(fdf, testbizid), ", top matches are:"
for i, (biz_id, sim, nc) in enumerate(tops):
    print i,businessname(fdf,biz_id), "| Sim", sim, "| Support",nc


# In[59]:

def get_top_recos_for_user(userid, df, dbase, n=5, k=7):
    bizs=get_user_top_choices(userid, df, numchoices=n)['business_id'].values
    rated_by_user=df[df.user_id==userid].business_id.values
    tops=[]
    for ele in bizs:
        t=knearest(ele, df.business_id.unique(), dbase, k=k)
        for e in t:
            #if e[0] not in rated_by_user:
                tops.append(e)
                
    #there might be repeats. unique it
    ids=[e[0] for e in tops]
    uids={k:0 for k in list(set(ids))}

    topsu=[]
    for e in tops:
        if uids[e[0]] == 0:
            topsu.append(e)
            uids[e[0]] =1
    topsr=[]     
    for r,s,nc in topsu:
        avg_rate=df[df.business_id==r].stars.mean()
        topsr.append((r, avg_rate))
        
    topsr=sorted(topsr, key=itemgetter(1), reverse=True)

    if n < len(topsr):
        return topsr[0:n]
    else:
        return topsr
#toprecos=get_top_recos_for_user(testuserid, Filtered, db, n=5, k=7)
#toprecos


# In[65]:

def get_user_top_choices(user_id, df, numchoices=5):
    "get the sorted top 5 restaurants for a user by the star rating the user gave them"
    udf=df[df.user_id==user_id][['business_id','stars']].sort(['stars'], ascending=False).head(numchoices)
    return udf
testuserid="7cR92zkDv4W3kqzii6axvg"
"""print "For", idname(Filtered,testuserid)+',', "top choices are:" 
bizs=get_user_top_choices(testuserid, fdf)['business_id'].values
[biznamefromid(fdf, biz_id) for biz_id in bizs]"""


# In[64]:

print "For user", idname(Filtered,testuserid)+',', "the top recommendations are:"
testuserid="7cR92zkDv4W3kqzii6axvg"
toprecos=get_top_recos_for_user(testuserid, Filtered, db, n=5, k=7)
for biz_id, biz_avg in toprecos: 
    print biznamefromid(Filtered,biz_id), "| Average Rating |", biz_avg

