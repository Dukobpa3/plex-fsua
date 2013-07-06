from descriptors import *

ICON = 'icon-default.png'
BASE_SITE_URL = "http://fs.to"  # "http://fs.ua"


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
def ItemsMenu(url):
    def ParseItems(url):
        items_page = HTML.ElementFromURL(url=url)
        items_elements = items_page.cssselect('.b-section-list .b-poster-section')

        parsed_items = []
        for item in items_elements:
            title_elem = item.cssselect('.m-full')[0]
            title = title_elem.xpath("string(span/text())")
            the_rest = title_elem.xpath("span/p/text()")
            if len(the_rest) == 1:
                original_title = ''
                year = the_rest[0]
            else:
                original_title, year = the_rest
            picture = title_elem.xpath("string(img/@src)")

            link = BASE_SITE_URL + item.xpath('string(a[@class="subject-link"]/@href)')

            parsed_items.append(ItemDescriptor(
                title=title,
                original_title=original_title,
                year=int(year.strip("()").split('-')[0]),
                poster=picture,
                link=link
            ))

        next_link = items_page.cssselect('.next-link')
        next_page = next_link and (BASE_SITE_URL + next_link[0].xpath("string(@href)"))

        return parsed_items, next_page

    items, next_page = ParseItems(url)
    items_menu_objects = [
        DirectoryObject(
            key=Callback(MovieMenu, title=item.title, original_title=item.original_title, year=item.year, poster=item.poster, link=item.link),
            title=item.title,
            summary='\n'.join(filter(None, [item.original_title, "(%d)" % item.year])),
            thumb=Resource.ContentsOfURLWithFallback(item.poster)
        ) for item in items
    ]

    if next_page:
        items_menu_objects.append(NextPageObject(
            key=Callback(ItemsMenu, url=next_page),
            title='Next...'
        ))

    items_menu = ObjectContainer(objects=items_menu_objects)

    return items_menu


@route('/video/fsua/movie')
def MovieMenu(**item_dict):
    def ParseMovie(item):
        movie_page = HTML.ElementFromURL(url=item['link'])

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

        item.update(additional_info)
        return MovieDescriptor(**item)

    movie = ParseMovie(item_dict)

    movie_object = MovieObject(
        title=movie.title,
        original_title=movie.original_title,
        year=movie.year,
        genres=movie.genres,
        directors=movie.directors,
        countries=movie.countries,
        thumb=movie.poster,
        url='http://fs.to/view/i418TqBqdu4hR4Y0wgUPtM4?play&file=1857596'
    )

    return ObjectContainer(objects=[movie_object])
