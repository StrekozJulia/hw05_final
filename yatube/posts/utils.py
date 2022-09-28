from django.core.paginator import Paginator, Page
from core.cached_paginator import CachedPaginator
from .models import Post

CACHE_TIMEOUT: int = 20


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
