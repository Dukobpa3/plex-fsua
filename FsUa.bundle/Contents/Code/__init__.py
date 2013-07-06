from descriptors import *


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

    @staticmethod
    def GetCurrent():
        if Prefs['sorting'] == "newness":
            return Sorting.NEW
        elif Prefs['sorting'] == "rating":
            return Sorting.RATING
        else:
            return Sorting.YEAR


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
    pass


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

            parsed_items.append(ItemDescriptor(
                title=title,
                original_title=original_title,
                year=year,
                poster=picture
            ))

        # previous_link = items_page.cssselect('.previous-link')
        prev_page = None  # previous_link and (BASE_SITE_URL + previous_link[0].xpath("string(@href)"))

        next_link = items_page.cssselect('.next-link')
        next_page = next_link and (BASE_SITE_URL + next_link[0].xpath("string(@href)"))

        return parsed_items, prev_page, next_page

    items, prev_page, next_page = ParseItems(url)
    items_menu_objects = [
        DirectoryObject(
            key=Callback(Stub),
            title=item.title,
            summary="&#xa;".join(filter(None, [item.original_title, item.year])),
            thumb=Resource.ContentsOfURLWithFallback(item.poster)
        ) for item in items
    ]
    # if prev_page:
    #     items_menu_objects.insert(0, DirectoryObject(
    #         key=Callback(ItemsMenu, url=prev_page),
    #         title='<--',
    #         summary="Previous page"
    #     ))
    if next_page:
        items_menu_objects.append(DirectoryObject(
            key=Callback(ItemsMenu, url=next_page),
            title='-->',
            summary="Next page"
        ))

    items_menu = ObjectContainer(objects=items_menu_objects)

    return items_menu


@route('/video/fsua/movie')
def MovieMenu():
    pass
