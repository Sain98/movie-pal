#!/usr/bin/python3
from bs4 import BeautifulSoup as bs
from requests import get
from re import findall
from json import loads, load


class mp():

    url = 'http://www.omdbapi.com/'
    parameters = {'apikey': ''}

    def __init__(self):
        pass

    def api():
        with open('config.json', 'r') as keyfile:
            mp.parameters['apikey'] = load(keyfile)["omdb_api_key"]

    def rotten():
        source = get('''https://www.rottentomatoes.com/
                    browse/in-theaters?minTomato=0
                    &maxTomato=100
                    &minPopcorn=0
                    &maxPopcorn=100
                    &genres=1;2;4;5;6;8;9;10;11;13;18;14&sortBy=release''').text
        soup = bs(source, 'lxml')
        js_source = soup.find_all("script")[38].prettify()
        final_json = findall('\[{.*}\]', js_source)
        try:
            final_json = loads(final_json[0])
        except IndexError:
            SystemExit('Error fetching data. Please retry.')
        finally:
            final_json = [i['title'] for i in final_json]
        return final_json

    def imdb():
        source = get(
            'http://www.imdb.com/movies-in-theaters/?ref_=nv_mv_inth_1').text
        soup = bs(source, 'lxml')
        titles = soup.find_all('td', {"class": "overview-top"})
        titles = [i.h4.a.text[:-7].lstrip() for i in titles]
        return titles

    def metac():
        ua_one = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
        ua_two = 'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
        headers = {

            'User-Agent': ua_one + ua_two}
        source = get(
            'http://www.metacritic.com/browse/movies/release-date/theaters/metascore', headers=headers).text
        soup = bs(source, 'lxml')
        imdb_movies = soup.find_all(
            'div', {'class': 'browse_list_wrapper wide'})

        titles_list = []
        for i in imdb_movies:
            scraped_titles = i.find_all('div', {'class': 'title'})
            titles = [title.text.rstrip().lstrip() for title in scraped_titles]
            titles_list.append(titles)
        return sum(titles_list, [])

    def in_theaters(key=""):
        site = key.lower()
        if key == "imdb":
            return mp.imdb()
        if key in ["rt", "rottentomatoes", "rotten tomatoes"]:
            return mp.rotten()
        if key in ['meta', 'metac', 'metacritic', 'mtc']:
            return mp.metac()

        return mp.merged_titles()

    def requester(key=""):
        rqst = get(mp.url, params=mp.parameters).json()
        movie = rqst
        if key == "":
            return movie
        try:
            return movie[key]
        except KeyError:
            raise SystemExit(f'That key doesn\'t seem available.\n Try any of these keys:\n\n{list(movie.keys())}')

    def merged_titles():
        tomatoes = mp.rotten()
        for i in mp.imdb():
            tomatoes.append(i)
        for i in mp.metac():
            tomatoes.append(i)
        return set(tomatoes)

    def search_title(self, key=""):
        mp.parameters['t'] = self
        return mp.requester(key)

    def search_id(self, key=""):
        mp.parameters['i'] = self
        return mp.requester(key)

    def rotten_search(movie, key="", printer=False):

        source = get(
            f'https://www.rottentomatoes.com/search/?search={movie}').text
        soup = bs(source, 'lxml')
        rotten_results = soup.find_all('script')
        for i in rotten_results:
            scraped_json = i.text.rstrip().lstrip()
            if scraped_json.startswith(
                    ("require(['jquery', 'globals', 'search-results',",
                        "'bootstrap'], function($, RT, mount)")):
                movies = findall('({.*})', scraped_json)[0]
                movies = loads(movies)

                if key == 'print':
                    printer = True

                if key == 'verbose':
                    links = [i["url"] for i in movies["movies"]]
                    for url in links:
                        mp.rotten_scraper(url, key='slug')

                if printer == True:
                    return mp.super_sort(movies)
                return movies

    def rotten_scraper(entry, the_year='', key=''):
        rotten_link = 'https://www.rottentomatoes.com{}{}{}'

        def link_mangler(entry):
            return entry.lower().replace(" ", "_")

        def the_url(year):

            if key == 'slug':
                link = rotten_link.format(entry, '', '')
            else:
                link = rotten_link.format('/', link_mangler(entry), year)
            return link

        def perform(source):
            the_page = source.text
            soup = bs(the_page, 'lxml')
            print(f'Page Title: "{soup.find("title").text}"')
            audience_review = ''
            rotten_rating = ''
            try:
                audience_review = soup.find(
                    'div',
                    {'class': 'audience-score'}).find(
                    'div',
                    {'class': 'meter-value'}).span.text
            except AttributeError:
                audience_review = soup.find(
                    'div', {'class': 'audience-score'}).find(
                        'div', {'class': 'noScore'}).text

            titles = soup.find('script', {'id': 'jsonLdSchema'}).text
            titles = loads(titles.encode('ascii', 'ignore').decode('ascii'))
            try:
                rotten_rating = str(
                    titles["aggregateRating"]["ratingValue"]) + "%"
            except KeyError:
                rotten_rating = 'Tomatometer Not Available'

            the_ratings = {"AudienceRating": audience_review,
                           "AverageRating": rotten_rating}
            if key == '':
                return the_ratings
            mp.sorter(the_ratings)
            print()

        def get_this(year):
            if year == '':
                return get(the_url(year))
            return get(the_url(f'_{year}'))

        if get_this(the_year).status_code == 404:
            raise SystemExit(
                "404 ERROR: \nThat didn't seem to work. Try entering a year or a different title.")
        return perform(get_this(the_year))

    def search(self, key=""):
        mp.parameters['s'] = self
        rqst = get(mp.url, params=mp.parameters)
        movie = rqst.json()["Search"]

        if key == "":
            return mp.key_loop(movie)

        items = []
        for i in movie:
            try:
                items.append(i[key])
            except KeyError:
                raise SystemExit(f'"{key}" is not an available key.',
                                 '\nTry: "Poster", "Title", "imdbID", or "Year"\n')
        return mp.looper(items)

    def display(self, printer=False, key=""):
        if isinstance(self, (list, set)):
            items = []
            for i in self:
                try:
                    movie = mp.search_title(i)
                except KeyError:
                    pass
                finally:
                    if movie["Response"] == 'False':
                        pass
                    if printer == True and key != "":
                        try:
                            print(movie[key])
                        except KeyError:
                            pass
                        except TypeError:
                            pass
                    elif printer == True:
                        print(str(movie).encode(
                            'ASCII', "ignore").decode('ascii'))
                        print()
                    elif printer == False and key != "":
                        try:
                            items.append(movie[key])
                        except KeyError:
                            pass
                        except TypeError:
                            pass
                    else:
                        items.append(movie)

            if printer == False:
                return items
        else:
            raise SystemExit("Please use a [ list ] or { set }!")

    def query(key="", the_site=""):
        if key == "":
            raise SystemExit('query() requires a key')
        the_query = mp.display(mp.in_theaters(site=the_site), key=key)
        return the_query

    def sorter(self):
        keys = list(self)
        for i in keys:
            print(f'{i}: {self[i]}')

    def looper(self):
        for i in self:
            if isinstance(i, dict):
                mp.key_loop(i)
            else:
                for i in self:
                    print(i)

    def key_loop(self):
        for i in self:
            for key, value in i.items():
                print(f'{key}: {value}')
            print()

    def super_sort(data, dict_key="movies"):
        for movie in data[dict_key]:
            print('-' * 20)
            for k, v in movie.items():
                if isinstance(movie[k], list):
                    if k == 'castItems':
                        print('Cast:')
                    else:
                        print(f'{k}:')
                    for x in movie[k]:
                        if isinstance(x, dict):
                            for key, value in x.items():
                                if key == "url":
                                    print(f'\t\t{key}: https://rottentomatoes.com{value}')
                                else:
                                    print(f'\t{key}: {value}')
                else:
                    print(f'{k}: {v}')

mp.api()
