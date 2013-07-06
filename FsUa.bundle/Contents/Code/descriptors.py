### Due to some stupid restrictions I haven't found the true way to implement this shit yet
#
# class Descriptor(object):
#     def __init__(self, **kwargs):
#         for k, v in kwargs.iteritems():
#             setattr(self, k, v)


class GenreDescriptor(object):
    def __init__(self, title, link):
        self.title = title
        self.link = link


class ItemDescriptor(object):
    def __init__(self, title, original_title, year, poster, link):
        self.title = unicode(title)
        self.original_title = unicode(original_title)
        self.year = int(year)
        self.poster = poster
        self.link = link


class MovieDescriptor(ItemDescriptor):
    def __init__(self,
                 title,
                 original_title,
                 year,
                 poster,
                 link,
                 duration=0,
                 rating=0,
                 genres=[],
                 countries=[],
                 directors=[],
                 summary=''):
        ItemDescriptor.__init__(self, title, original_title, year, poster, link)
        self.duration = duration
        self.rating = rating
        self.genres = genres
        self.countries = countries
        self.directors = directors
        self.summary = unicode(summary)
