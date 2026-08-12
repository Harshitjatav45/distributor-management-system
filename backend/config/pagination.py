from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """Applied project-wide via REST_FRAMEWORK['DEFAULT_PAGINATION_CLASS'].
    page_size_query_param lets a caller request a larger single page (e.g.
    the frontend fetching "all items for this one purchase/sales header",
    which is always a small, bounded set) without needing multi-page
    fetch logic for that specific case.
    """
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 200
