from rest_framework import status
from rest_framework.test import APITestCase

from drf.views import PostListCreateView
from drf.models import Author, Post, Location, Comment


class PostTests(APITestCase):

    def test_create_post_comment(self):
        """
        Test if we can create new post and comment objects.
        """
        Author.objects.create_user(username='test', email='gangfu1982@gmail.com', password='test')
        self.client.login(username='test', password='test')
        data_post = { 
                 'title': 'aaa', 
                 'content': 'abc', 
                 'location': 
                     { 
                       'name': 'a', 
                       'address': '6010 california circle, rockville, md'
                     }, 
                 'images':[], 
                 'bookingoptions': [] 
               }
        response = self.client.post('/post/', data_post, format='json')
        print response.content
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)

        data_comment1 = {
                 'rating': '9', 
                 'content': 'good', 
                 'post_id': '1'
               }
        response = self.client.post('/comment/', data_comment1, format='json')
        print response.content
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)

        data_comment2 = {
                 'rating': '9', 
                 'content': 'good', 
                 'post_id': '1', 
                 'parent_id': '1'
               }
        response = self.client.post('/comment/', data_comment2, format='json')
        print response.content
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 2)


