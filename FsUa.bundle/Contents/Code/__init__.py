from descriptors import *
import sys

ICON = 'icon-default.png'
BASE_SITE_URL = "http://fs.to"  # "http://fs.ua"
SEARCH_URL = "http://fs.to/video/search.aspx?search=%s"


class MediaCategoryType:
    FILMS = '0'
    SERIALS = '1'
    CARTOONS = '2'
    CARTOONSERIALS = '3'


class Sorting:
    NEW = 'sort=new'
    RATING = 'sort=rating'
    YEAR = 'sort=year'

    @classmethod
    def GetCurrent(cls):
        if Prefs['sorting'] == "newness":
            return cls.NEW
        elif Prefs['sorting'] == "rating":
            return cls.RATING
        else:
            return cls.YEAR


MEDIA_CATEGORY = {
    MediaCategoryType.FILMS: {
        'title': "Films",
        'genre_url': 'http://fs.to/video/films/group/film_genre/',
    },
    MediaCategoryType.SERIALS: {
        'title': "Serials",
        'genre_url': 'http://fs.to/video/serials/group/genre/',
    },
    MediaCategoryType.CARTOONS: {
        'title': "Cartoons",
        'genre_url': 'http://fs.to/video/cartoons/group/cartoon_genre/',
    },
    MediaCategoryType.CARTOONSERIALS: {
        'title': "Cartoon Serials",
        'genre_url': 'http://fs.to/video/cartoonserials/group/genre/',
    }
}


def Start():
    DirectoryObject.thumb = R(ICON)


@handler('/video/fsua', 'FS.ua')
def MainMenu():
    main_menu = ObjectContainer(
        objects=[
            DirectoryObject(
                title=value['title'],
                key=Callback(MediaCategoryMenu, media_category=key)
            ) for key, value in MEDIA_CATEGORY.iteritems()
        ]
    )
    main_menu.add(InputDirectoryObject(
        title="Search",
        prompt="Search for...",
        key=Callback(Search)
    ))
    main_menu.add(PrefsObject(title="Settings"))

    return main_menu


@route('/video/fsua/stub', method='GET')
def Stub():
    return 'bla'


@route('/video/fsua/media-category', method='GET')
def MediaCategoryMenu(media_category):
    media_category_menu = ObjectContainer(
        objects=[
            DirectoryObject(
                title="Genres",
                key=Callback(GenresMenu, media_category=media_category)
            )
        ]
    )

    return media_category_menu


@route('/video/fsua/genres', method='GET')
def GenresMenu(media_category):
    def ParseGenres(media_category):
        '''Return list of tuples in the following form: (genre_title, genre_url)'''

        url = MEDIA_CATEGORY[media_category]['genre_url']
        genres_page = HTML.ElementFromURL(url)
        genre_selector = url.split('/')[-2]
        genre_elements = genres_page.cssselect('.%s .b-list-links > li:not([class=noitems]) > a' % genre_selector)

        parsed_genres = [
            GenreDescriptor(
                title=genre.xpath("string(text())"),
                link=BASE_SITE_URL + genre.xpath("string(@href)")
            ) for genre in genre_elements
        ]

        return parsed_genres

    genres = ParseGenres(media_category)
    genres_menu = ObjectContainer(
        objects=[
            DirectoryObject(
                title=genre.title,
                summary=genre.link,
                key=Callback(ItemsMenu, url="{url}?{args}".format(url=genre.link, args=Sorting.GetCurrent()))
            ) for genre in genres
        ]
    )

    return genres_menu


@route('/video/fsua/items', methods='GET')
def ItemsMenu(url, page=0):
    results = {}
    next_page = {'val': False}

    @parallelize
    def ParseItems():
        page_url = "{url}&page={page}".format(url=url, page=page) if page > 0 else url
        items_page = HTML.ElementFromURL(url=page_url)
        items_elements = items_page.cssselect('.b-section-list .b-poster-tile')  # .b-poster-section

        next_page['val'] = items_page.cssselect('.next-link') is not None
        verb1=len(items_elements)
        Log('elm cnt:%s', verb1)

        for num in range(len(items_elements)):
            item = items_elements[num]
            title_elem = item.cssselect('.b-poster-tile__title-full')[0]
#            Log('titleelm:%s',title_elem)

            title = title_elem.xpath("string(text())").strip()

            the_rest = item.cssselect(".b-poster-tile__title-info-items")
            if len(the_rest) == 1:
                original_title = the_rest[0].text
                year = original_title.split('●')[0]
            year = int(year.strip("()"))

            link = BASE_SITE_URL + item.xpath('string(a[@class="b-poster-tile__link"]/@href)')

            descr = {
                'title': title,
                'original_title': original_title,
                'year': year,
                'link': link
            }
#            Log('ds:%s',descr)

            @task
            def ParseMovie(link=link, descr=descr, num=num):
                movie_page = HTML.ElementFromURL(link)

                additional_info = {}
                additional_info['summary'] = movie_page.cssselect('.b-tab-item__description p')[0].text_content()
                additional_info['poster'] = movie_page.cssselect('.poster-main img')[0].xpath('string(@src)')

                info_table = movie_page.cssselect('.item-info tr')
                for row in info_table:
                    caption_elem, values_elem = row.xpath('td')
                    caption = caption_elem.xpath('string(text())').strip()
#                    values = values_elem.text_content().strip()
                    values = values_elem.xpath('span/a/span/text()')
                    if caption == 'Жанр:':
                        additional_info['genres'] = values
                    elif caption == 'Страна:':
                        additional_info['countries'] = values_elem.xpath('a/span/text()')
                    elif caption == 'Режиссёр:':
                        additional_info['directors'] = values

                additional_info['media_url'] = BASE_SITE_URL + movie_page.cssselect('.b-view-material')[0].xpath('string(a/@href)')
#                Log('ainfo: %s', additional_info);


                descr.update(additional_info)
                results[num] = MovieDescriptor(**descr)

    keys = results.keys()
    keys.sort()

    items_menu_objects = [results[key].ToMovieObject() for key in keys]

    if next_page['val']:
        items_menu_objects.append(NextPageObject(
            key=Callback(ItemsMenu, url=url, page=page+1),
            title='>> Page {page}'.format(page=page+2)
        ))

    items_menu = ObjectContainer(objects=items_menu_objects)
#    Log('url: %s', HTTPLiveStreamURL('http://fs.to/video/films/view/iw4TKfLYcDBeUZ71ZHmwTe'));
#    items_menu = ObjectContainer(objects = [MovieObject(
#        title='ya video',
#        url='http://fs.to/video/films/view/iw4TKfLYcDBeUZ71ZHmwTe',
#        url='http://fs.to/view/iw4TKfLYcDBeUZ71ZHmwTe',
#     )])

    return items_menu


@route('/video/fsua/search/{query}')
def Search(query):
    results = {}

    @parallelize
    def ParseItems():
        result_page = HTML.ElementFromURL(SEARCH_URL % String.Quote(query, usePlus=True))
        results_elements = result_page.cssselect('.b-search-results table:first-of-type tr .image-wrap')

        for num in range(len(results_elements)):
            result = results_elements[num]
            title_elem = result.xpath('string(a/@title)')

            Log.Debug(title_elem)
            if title_elem.find('/') >= 0:
                telm_split = title_elem.split('/')
                title = telm_split[0]
                the_rest = ''
                for num in range(1, len(telm_split)):
                    the_rest = the_rest + '/' + telm_split[num] 
                title = title.strip()
            else:
                begin_id = title_elem.find('(')
                title = title_elem[1:begin_id]
                the_rest = title_elem[begin_id:len(title_elem)]
                title = title.strip()

            split_char = the_rest.rfind(' ')
            original_title = the_rest[:split_char].strip()
            year = int(the_rest[split_char + 1:].strip('( )').split('-')[0])

            link = BASE_SITE_URL + result.xpath('string(a/@href)')

            descr = {
                'title': title,
                'original_title': original_title,
                'year': year,
                'link': link
            }

            @task
            def ParseMovie(link=link, descr=descr, num=num):
                try:
                    movie_page = HTML.ElementFromURL(link)
                    Log('url:%s', link)

                    additional_info = {}
                    if len(movie_page.cssselect('.b-tab-item__description p')) <= 0:
                        results[num] = None
                        return
                    
                    additional_info['summary'] = movie_page.cssselect('.b-tab-item__description p')[0].text_content()
                    additional_info['poster'] = movie_page.cssselect('.poster-main img')[0].xpath('string(@src)')

                    info_table = movie_page.cssselect('.item-info tr')
                    for row in info_table:
                        caption_elem, values_elem = row.xpath('td')
                        caption = caption_elem.xpath('string(text())').strip()
                        values = values_elem.xpath('span/a/span/text()')
                        if caption == 'Жанр:':
                            additional_info['genres'] = values
                        elif caption == 'Страна:':
                            additional_info['countries'] = values_elem.xpath('a/span/text()')
                        elif caption == 'Режиссёр:':
                            additional_info['directors'] = values

                    additional_info['media_url'] = BASE_SITE_URL + movie_page.cssselect('.b-view-material')[0].xpath('string(a/@href)')

                    descr.update(additional_info)
                    results[num] = MovieDescriptor(**descr)
                except:
                    e = sys.exc_info()[1]
                    Log.Error('Error in ParseMovie url:%s error:%s', link, e)
                    results[num] = None
                    return

    keys = results.keys()
    keys.sort()

    results_menu_objects = [];
    for key in keys:
        if not results[key] is None:
            results_menu_objects.append(results[key].ToMovieObject())
    results_menu = ObjectContainer(objects=results_menu_objects)

    return results_menu
