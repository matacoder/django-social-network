from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.shortcuts import reverse
from .models import Group, Post
from django.core.files import File
from django.core.cache import cache

User = get_user_model()


class TestPostsAndLogin(TestCase):
    def setUp(self):
        """ Preparing test enviroment """
        self.client = Client()
        self.client_cache = Client()
        self.client_unauthorized = Client()
        # create user
        self.user = User.objects.create_user(
            username="sarah", email="connor.s@skynet.com", password="12345"
        )
        # create group
        self.testgroup = Group.objects.create(
            title="Test Group",
            slug="group",
            description="Testing Around",
        )
        self.testgroup2 = Group.objects.create(
            title="Test Group 2",
            slug="group2",
            description="Testing Around 2",
        )
        # create post
        with open('posts/file.jpg', 'rb') as img:
            self.post = Post.objects.create(
                text=("You're talking about things I haven't"
                      " done yet in the past tense. It's driving me crazy!"),
                author=self.user,
                group=self.testgroup,
                image=File(img)
            )
        # login
        self.client.force_login(self.user, backend=None)
        cache.clear()

    def test_post_with_image(self):
        """ Post with image is added """
        url = reverse('new_post')
        with open('posts/file.jpg', 'rb') as img:
            data = {
                'text': 'Abracadabra with image',
                'group': self.testgroup.id,
                'image': img
            }
            response = self.client.post(url, data=data, follow=True)
            cache.clear()
            self.assertEqual(response.status_code, 200)
            urls = self.generate_urls()
            for url in urls:
                response = self.client.get(url)
                self.assertIn('img'.encode(), response.content)

    def test_non_img_file(self):
        """ Test uploading non-image file README.md """
        url = reverse('new_post')
        with open('README.md', 'rb') as img:
            data = {
                'text': 'Abracadabra with non-image',
                'group': self.testgroup.id,
                'image': img
            }
            cache.clear()
            response = self.client.post(url, data=data)
            self.assertFalse(response.context['form'].is_valid())

    def generate_urls(self):
        index = reverse("index")
        profile = reverse("profile", args=[self.user.username])
        post = reverse("post_single", args=[self.user.username, 2])
        group = reverse("group_url", args=[self.testgroup.slug])
        return [index, profile, post, group]

    def test_register_url(self):
        """ Test user profile """
        response = self.client.get(
            reverse("profile", args=[self.user.username])
        )
        self.assertEqual(response.status_code, 200)

    def test_404_url(self):
        """ Test 404 """
        response = self.client.get('/404error/')
        self.assertEqual(response.status_code, 404)

    def test_logged_in_post(self):
        """ Test post creating """
        response = self.client.post(
            reverse("new_post"),
            {
                "text": "New post",
                "author": self.user
            },
            follow=True
        )
        cache.clear()
        lastpost = Post.objects.latest("pub_date")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(lastpost.text, "New post")

    def check_unauthorized(self, response):
        """ Check unauthorized attempt """
        loginurl = reverse("login")
        newposturl = reverse("new_post")
        url = f"{loginurl}?next={newposturl}"
        self.assertRedirects(
            response,
            url,
            status_code=302, target_status_code=200
        )

    def test_not_logged_redirect(self):
        """ Test unauthorized posting """
        response = self.client_unauthorized.get(reverse("new_post"))
        self.check_unauthorized(response)
        response = self.client_unauthorized.post(
            reverse("new_post"),
            {
                "text": "Unreg post",
                "author": self.user
            }
        )
        self.check_unauthorized(response)
        response = self.client_unauthorized.get(
            reverse("new_post")
        )
        self.check_unauthorized(response)
        # Check in DB
        lastpost = Post.objects.latest("pub_date")
        self.assertNotEqual(lastpost.text, "Unreg post")

    def test_new_post(self):
        """ Test fixture post in various areas """
        self.check_if_post_is_displaying(self.post, self.testgroup)

    def test_logged_in_edit_show(self):
        """ Logged in user can edit post """
        response = self.client.post(
            reverse("post_edit", args=[self.user.username, self.post.pk]),
            {
                "text": "Edited post",
                "author": self.user,
                "group": self.testgroup2.id
            },
            follow=True
        )
        editedpost = Post.objects.get(pk=self.post.pk)
        self.assertEqual(response.status_code, 200)
        # test all pages
        self.check_if_post_is_displaying(editedpost, self.testgroup2)
        # test if previous group page is empty
        oldgroupurl = reverse("group_url", args=[self.testgroup.slug])
        response = self.client.get(oldgroupurl)
        self.assertEqual(len(response.context["page"]), 0)

    def check_if_post_is_displaying(self, post_to_compare, group_object):
        """ Test displaying in various areas """
        # index
        response = self.client.get(reverse("index"))
        self.detail_multipost_comparison(response, post_to_compare)

        # profile
        response = self.client.get(
            reverse("profile", args=[self.user.username])
        )
        self.detail_multipost_comparison(response, post_to_compare)

        # post
        response = self.client.get(
            reverse("post_single", args=[self.user.username, self.post.pk])
        )
        self.detail_singlepost_comparison(response, post_to_compare)

        # group
        response = self.client.get(
            reverse("group_url", args=[group_object.slug])
        )
        self.detail_multipost_comparison(response, post_to_compare)

    def detail_multipost_comparison(self, response, post_to_compare):
        """ Extract first post of array """
        page = response.context["page"]
        post = page[0]
        self.post_comparison(response, post, post_to_compare)

    def detail_singlepost_comparison(self, response, post_to_compare):
        """ Take the only post in context """
        post = response.context["post"]
        self.post_comparison(response, post, post_to_compare)

    def post_comparison(self, response, post, post_to_compare):
        """ Actual compararing process """
        self.assertEqual(response.status_code, 200)
        post_one = (post.text, post.id, post.author, post.group,)
        post_two = (
            post_to_compare.text,
            post_to_compare.id,
            post_to_compare.author,
            post_to_compare.group,
        )
        self.assertEqual(post_one, post_two)

    def test_cache(self):
        """ Test 20 sec index cache """
        response = self.client.get(reverse('index'))
        cache = response['Cache-Control']
        self.assertEqual(cache, 'max-age=20')
