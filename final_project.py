import pandas as pd
from numpy import trapz
import json
import matplotlib.pyplot as plt
import seaborn as sns
import requests

pd.set_option('expand_frame_repr', False)

## begin here if getting data from TMDB

# get api key
# there should be a 'keys.txt' in your directory with just your API key for this to work
# optionally, just assign api_key to whatever your api key is

with open("keys.txt", "r") as keys:
    api_key = keys.read().strip()

# script

movie_json = []
with open('movie_ids.json', 'r', encoding="utf8") as file:
    for line in file:
        movie_json.append(json.loads(line))
        
rows = []

for item in movie_json:
    rows.append(list(item.values()))
    
movies_id = pd.DataFrame(rows, columns=list(movie_json[0].keys()))

pop_id = movies_id[movies_id['popularity'] > 100].reset_index(drop=True)

# get information from api

def get_info(page, genre_num, main_dat):
    link = ("https://api.themoviedb.org/3/discover/movie?api_key=" + 
            api_key + 
            "&language=en-US&sort_by=release_date.desc&page=" +
            str(page) +
            "&with_genres=" +
            str(genre_num))
        
    response = requests.get(link)
    
    if response.status_code == 200:
        data = response.json()  # Assuming the response is in JSON format
        # Process the data as needed
    else:
        print("Error:", response.status_code)
    
    dat = pd.DataFrame(data)
    
    dat = dat['results']
    
    dat = pd.DataFrame(dat.tolist())
    
    # selecting cols
    dat = dat[['adult', 'genre_ids', 'original_title', 'popularity', 
               'vote_average', 'vote_count', 'release_date']]
    
    # selecting only movies with a substantial count of votes
    # this also helps in excluding movies which are not released yet!
    
    dat = dat[dat['vote_count'] > 0]
    
    return(pd.concat([main_dat, dat]))
    
# get info for horror movies id 27

dat_horror = pd.DataFrame()

for page in range(1, 501):
    dat_horror = get_info(page, genre_num=27, main_dat=dat_horror) 
    print("Page " + str(page) + " obtained successfully. Moving on to next page.")

# get info for action movies id 28

dat_action = pd.DataFrame()

for page in range(1, 501):
    dat_action = get_info(page, genre_num=28, main_dat=dat_action) 
    print("Page " + str(page) + " obtained successfully. Moving on to next page.")

# putting both together

dat_horror['genre'] = 'horror'

dat_action['genre'] = 'action'

dat_all = pd.concat([dat_horror, dat_action])

# save csv

#dat_all.to_csv('movie_data.csv', index=False)

## begin here with .csv file
## load csv

dat_all = pd.read_csv('movie_data.csv')

# plotting
# we'll use a subsample with popularity lower than 100 due to 
# a few outlier movies with extremely high popularity values

movies = dat_all[dat_all['popularity'] < 100]

# due to the way I downloaded data, information on horror movies
# does not go back in the past as much as action movies
# we'll need to select a subsample in which the timings match.

min_horror = min(movies[movies['genre'] == 'horror']['release_date'])
min_action = min(movies[movies['genre'] == 'action']['release_date'])

# as demonstrated by this, horror movies only go back to 2019,
# while action movies go back to 2014. we'll only look from 2019-01-06 beyond.

movies = movies[movies['release_date'] > '2019-01-06']

# first plot: line plot of monthly median popularity for action and horror

# calculate median ratings per month of each year

# transform date to datetime

movies['date'] = pd.to_datetime(movies['release_date'])

mov_median = (movies.groupby(['genre', pd.Grouper(key='date', freq='M')])['popularity']
              .median()
              .reset_index())

mov_median['zero'] = 0
sub_horror = mov_median[mov_median['genre'] == 'horror']
sub_action = mov_median[mov_median['genre'] == 'action']

# last minute tidying

mov_median['Movie genre'] = mov_median['genre'].replace({'action':'Action', 'horror':'Horror'})

# plot

sns.set_style("white")

sns.lineplot(mov_median, x='date', y='popularity', hue='Movie genre')

plt.fill_between(data=sub_action, 
                 x='date', y1='popularity', y2='zero',
                 where=(sub_horror['popularity'] > 0),
                 alpha=.1, color="blue")

plt.fill_between(data=sub_horror, 
                 x='date', y1='popularity', y2='zero',
                 where=(sub_horror['popularity'] > 0),
                 alpha=.2, color="orange")

plt.xticks(rotation=30)

plt.xlabel(None)
plt.ylabel('Monthly median popularity', fontsize=12)
plt.title('Popularity in action and horror movies in recent years',
          fontsize=14)

plt.savefig('fig1.png', bbox_inches='tight', dpi=600)

# + area under the curve

auc = pd.DataFrame({'Area under the curve': [
    trapz(sub_action['popularity']),
    trapz(sub_horror['popularity'])
    ],
    "Movie genre":["Action", "Horror"]}) 


sns.barplot(auc, y='Area under the curve', x="Movie genre",
            width=.35, edgecolor=".15")

plt.xlabel(None)
plt.ylabel('Area under the curve', fontsize=12)
plt.title('Popularity in action and horror movies in recent years',
          fontsize=14)

plt.savefig('fig1_5.png', bbox_inches='tight', dpi=600)


# second plot: popularity and vote score

sns.jointplot(movies[movies['popularity'] > 10], x='popularity', y='vote_average', kind="reg", color="#4CB391",
              scatter_kws={'alpha':0.3}).fig.tight_layout()

plt.xlabel("Popularity (> 10)", fontsize=14)
plt.ylabel('Movie score', fontsize=14)
plt.title('Association between popularity and average movie score',
          fontsize=16, pad=75)

plt.savefig('fig2.png', bbox_inches='tight', dpi=600)

