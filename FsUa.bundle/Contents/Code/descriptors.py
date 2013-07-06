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
    def __init__(self, title, original_title, year, poster):
        self.title = title
        self.original_title = original_title
        self.year = year
        self.poster = poster
