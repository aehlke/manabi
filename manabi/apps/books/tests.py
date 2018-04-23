from django.test import TestCase
from .models import Textbook


class SimpleTest(TestCase):
    def setUp(self):
        self.book = Textbook(isbn='4789011623') # Genki textbook

    #TODO-OLD
    #def test_get_image_url(self):
    #    urls = self.book.get_image_urls()
    #    self.assertTrue(urls)
    #    self.assertTrue(urls['medium'])
    #    self.assertTrue('images-amazon.com/images' in urls['small'])

    #def test_get_info(self):
    #    info = self.book.get_basic_info()
    #    self.assertTrue('Banno' in info['author'],
    #                    'Expected Banno in author, got ' + info['author'])
    #    self.assertTrue('Genki' in info['title'])

    #def test_isbn_13(self):
    #    for isbn in ['9784770030412', '978-4770030412']:
    #        book = Textbook(isbn=isbn) # Exploring Japanese Literature
    #        info = book.get_basic_info()
    #        self.assertTrue('Japanese' in info['title'])


