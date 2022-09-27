from django.core.cache import cache
from django.core.paginator import Paginator, Page
from .models import Post

CACHE_TIMEOUT: int = 20


class CachedPaginator(Paginator):
    """A paginator that caches the results on a page by page basis."""
    def __init__(self,
                 object_list,
                 per_page,
                 cache_key,
                 cache_timeout=300,
                 orphans=0,
                 allow_empty_first_page=True):
        super(CachedPaginator, self).__init__(object_list,
                                              per_page,
                                              orphans,
                                              allow_empty_first_page)
        self.cache_key = cache_key
        self.cache_timeout = cache_timeout

    def page(self, number):
        """
        Returns a Page object for the given 1-based page number.

        This will attempt to pull the results out of the cache first, based on
        the number of objects per page and the requested page number. If not
        found in the cache, it will pull a fresh list and then cache that
        result.
        """
        if number is None:
            number = 1
        number = self.validate_number(number)
        cached_object_list = cache.get(self.build_cache_key(number), None)

        if cached_object_list is not None:
            page = Page(cached_object_list, number, self)
        else:
            page = super(CachedPaginator, self).page(number)
            # Since the results are fresh, cache it.
            cache.set(self.build_cache_key(number),
                      page.object_list,
                      self.cache_timeout)

        return page

    def build_cache_key(self, page_number):
        """Appends the relevant pagination bits to the cache key."""
        return "%s:%s:%s" % (self.cache_key, self.per_page, page_number)


def create_page(posts: Post,
                page_number: int,
                posts_on_page: int,
                cache_key: str) -> Page:
    paginator = CachedPaginator(posts,
                                posts_on_page,
                                cache_key,
                                CACHE_TIMEOUT
                                )
    page_obj = paginator.page(page_number)
    return page_obj


def create_page_not_cached(posts: Post,
                           page_number: int,
                           posts_on_page: int) -> Page:
    paginator = Paginator(posts, posts_on_page)
    page_obj = paginator.get_page(page_number)
    return page_obj
