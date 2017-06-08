from unittest import TestCase as PythonTestCase
from wikimedia_thumbor.loader import are_request_dimensions_valid


class MockRequest(object):
    def __init__(self, width, page=1):
        self.width = width
        self.page = page


class MockContext(object):
    def __init__(self, request):
        self.request = request


class WikimediaLoaderTest(PythonTestCase):
    def test_empty_x_content_dimensions(self):
        context = MockContext(MockRequest(5000))
        result = are_request_dimensions_valid(context, '')
        assert result is True

    def test_malformed_x_content_dimensions(self):
        context = MockContext(MockRequest(5000))
        result = are_request_dimensions_valid(context, '5174x3288')
        assert result is True
        result = are_request_dimensions_valid(context, 'fooxbar:1')
        assert result is True
        result = are_request_dimensions_valid(context, '5300x200:1/5174x3288:foo-10')
        assert result is True
        result = are_request_dimensions_valid(context, '5174x3288:foo')
        assert result is True

    def test_smaller_than_single_page(self):
        context = MockContext(MockRequest(5000))
        result = are_request_dimensions_valid(context, '5174x3288:1')
        assert result is True

    def test_equal_to_single_page(self):
        context = MockContext(MockRequest(5174))
        result = are_request_dimensions_valid(context, '5174x3288:1')
        assert result is False

    def test_bigger_than_single_page(self):
        context = MockContext(MockRequest(5200))
        result = are_request_dimensions_valid(context, '5174x3288:1')
        assert result is False

    def test_bigger_than_page_in_range(self):
        context = MockContext(MockRequest(5200, 7))
        result = are_request_dimensions_valid(context, '5300x200:1/5174x3288:2-10')
        assert result is False

    def test_bigger_than_page_in_list(self):
        context = MockContext(MockRequest(5200, 5))
        result = are_request_dimensions_valid(context, '5300x200:1-2,4,6/5174x3288:3,5,7')
        assert result is False
