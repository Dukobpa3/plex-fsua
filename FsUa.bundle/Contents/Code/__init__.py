from descriptors import *

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
        genres_page = HTML.ElementFromURL(url=url)
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
        items_elements = items_page.cssselect('.b-section-list .b-poster-section')

        next_page['val'] = items_page.cssselect('.next-link') is not None

        for num in range(len(items_elements)):
            item = items_elements[num]
            title_elem = item.cssselect('.m-full')[0]

            title = title_elem.xpath("string(span/text())")

            the_rest = title_elem.xpath("span/p/text()")
            if len(the_rest) == 1:
                original_title = ''
                year = the_rest[0]
            else:
                original_title, year = the_rest
            year = int(year.strip("()").split('-')[0])

            link = BASE_SITE_URL + item.xpath('string(a[@class="subject-link"]/@href)')

            descr = {
                'title': title,
                'original_title': original_title,
                'year': year,
                'link': link
            }

            @task
            def ParseMovie(link=link, descr=descr, num=num):
                movie_page = HTML.ElementFromURL(link)

                additional_info = {}
                additional_info['summary'] = movie_page.cssselect('.item-info > p')[0].text_content()
                additional_info['poster'] = movie_page.cssselect('.poster-main img')[0].xpath('string(@src)')

                info_table = movie_page.cssselect('.item-info tr')
                for row in info_table:
                    caption_elem, values_elem = row.xpath('td')
                    caption = caption_elem.xpath('string(text())').strip()
                    values = values_elem.xpath('a/text()')
                    if caption == 'Жанр:':
                        additional_info['genres'] = values
                    elif caption == 'Страна:':
                        additional_info['countries'] = values
                    elif caption == 'Режиссёр:':
                        additional_info['directors'] = values

                additional_info['media_url'] = BASE_SITE_URL + movie_page.cssselect('.b-view-material')[0].xpath('string(a/@href)')

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
            title, the_rest = title_elem.split('/')
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
                movie_page = HTML.ElementFromURL(link)

                additional_info = {}
                additional_info['summary'] = movie_page.cssselect('.item-info > p')[0].text_content()
                additional_info['poster'] = movie_page.cssselect('.poster-main img')[0].xpath('string(@src)')

                info_table = movie_page.cssselect('.item-info tr')
                for row in info_table:
                    caption_elem, values_elem = row.xpath('td')
                    caption = caption_elem.xpath('string(text())').strip()
                    values = values_elem.xpath('a/text()')
                    if caption == 'Жанр:':
                        additional_info['genres'] = values
                    elif caption == 'Страна:':
                        additional_info['countries'] = values
                    elif caption == 'Режиссёр:':
                        additional_info['directors'] = values

                additional_info['media_url'] = BASE_SITE_URL + movie_page.cssselect('.b-view-material')[0].xpath('string(a/@href)')

                descr.update(additional_info)
                results[num] = MovieDescriptor(**descr)

    keys = results.keys()
    keys.sort()

    results_menu_objects = [results[key].ToMovieObject() for key in keys]
    results_menu = ObjectContainer(objects=results_menu_objects)

    return results_menu
