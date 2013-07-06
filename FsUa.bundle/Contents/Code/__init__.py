class MediaCategoryType:
    FILMS = '0'
    SERIALS = '1'
    CARTOONS = '2'
    CARTOONSERIALS = '3'


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

        parsed_genres = [(genre.xpath("string(text())"), genre.xpath("string(@href)")) for genre in genre_elements]

        return parsed_genres

    genres = ParseGenres(media_category)
    genres_menu = ObjectContainer(
        objects=[
            DirectoryObject(
                title=title,
                summary=link,
                key=Callback(Stub)
            ) for title, link in genres
        ]
    )

    return genres_menu




@route('/video/fsua/items', methods='GET')
def ItemsMenu(url):
    def ParseItems(url):
        items_page = HTML.ElementFromURL(url=url)
        items_elements = items.page.cssselect('.b-section-list .b-poster-section')

        parsed_items = [
            
        ]

    pass


