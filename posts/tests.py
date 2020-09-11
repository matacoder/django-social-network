from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import reverse
from django.test import Client, TestCase

from .models import Comment, Follow, Group, Post

User = get_user_model()


class TestPostsAndLogin(TestCase):
    def setUp(self):
        """ Preparing test enviroment """
        self.client = Client()
        self.client_unauthorized = Client()
        # create user
        self.user = User.objects.create_user(
            username="sarah", email="connor.s@skynet.com", password="12345"
        )
        # create follow user
        self.author = User.objects.create_user(
            username="skynet", email="admin@skynet.com", password="12345"
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
        self.post = Post.objects.create(
            text=("Youre talking about things I havent"
                  " done yet in the past tense. Its driving me crazy!"),
            author=self.user,
            group=self.testgroup
        )
        
        # login
        self.client.force_login(self.user, backend=None)
        cache.clear()

    def test_post_with_image(self):
        """ Post with image is added """
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04"
            b"\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02"
            b"\x02\x4c\x01\x00\x3b"
        )
        img = SimpleUploadedFile(
            "small.gif",
            small_gif,
            content_type="image/gif"
        )
        url = reverse("new_post")
        data = {
            "text": "Abracadabra with image",
            "group": self.testgroup.id,
            "image": img
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        urls = self.generate_urls()
        for url in urls:
            response = self.client.get(url)
            self.assertIn("<img".encode(), response.content)

    def test_non_img_file(self):
        """ Test uploading non-image file """
        wrong_file = (
            b"\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02"
            b"\x02\x4c\x01\x00\x3b"
        )
        self.wrong = SimpleUploadedFile(
            "wrong_file.doc",
            wrong_file,
            content_type="doc"
        )
        url = reverse("new_post")
        data = {
            "text": "Abracadabra with non-image",
            "group": self.testgroup.id,
            "image": self.wrong
        }
        response = self.client.post(url, data=data)
        self.assertFormError(
            response,
            form="form",
            field="image",
            errors="Загрузите правильное изображение. Файл, "
                   "который вы загрузили, поврежден или не "
                   "является изображением.")

    def generate_urls(self):
        lastpost = Post.objects.latest("pub_date")
        index = reverse("index")
        profile = reverse("profile", args=[self.user.username])
        post = reverse("post_single", args=[self.user.username, lastpost.pk])
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
        response = self.client.get("/404error/")
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
        response = self.client.get(reverse("index"))
        cache_test = response["Cache-Control"]
        self.assertEqual(cache_test, "max-age=20")
        self.assertEqual(len(response.context["page"]), 1)
        # create skynet post
        self.post_skynet = Post.objects.create(
            text="Skynet test",
            author=self.author,
            group=self.testgroup
        )
        response = self.client.get(reverse("index"))
        self.assertIsNone(response.context)
        cache.clear()
        response = self.client.get(reverse("index"))
        self.assertEqual(len(response.context["page"]), 2)

    def test_logged_in_subscribe(self):
        """ Logged in can subscribe to authors """
        response = self.client.get(
            reverse("profile_follow", args=["skynet"]),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Follow.objects.filter(
            user=self.user, author=self.author).exists()
        )

    def test_logged_in_unsubscribe(self):
        """ Logged in can unsubscribe from authors """
        Follow.objects.create(user=self.user, author=self.author)
        response = self.client.get(
            reverse("profile_unfollow", args=["skynet"]),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        num = Follow.objects.filter(user=self.user, author=self.author).count()
        self.assertEqual(num, 0)

    def test_logged_out_subscribe(self):
        """ Logged out can not subscribe to authors """
        response = self.client_unauthorized.get(
            reverse("profile_follow", args=["sarah"])
        )
        self.assertEqual(response.status_code, 302)
        num = Follow.objects.filter(author=self.user).count()
        self.assertEqual(num, 0)

    def test_new_post_on_follow_page(self):
        """ New post displays on follow page
            of subscribed authors and does not
            display if author not followed """

        Follow.objects.create(user=self.user, author=self.author)
        # create skynet post
        post_skynet = Post.objects.create(
            text="Skynet test displaying",
            author=self.author,
            group=self.testgroup
        )
        # check if post shows up
        display_resp = self.client.get(
            reverse("follow_index"),
        )
        page = display_resp.context["page"]
        post = page[0]
        self.assertEqual(
            post_skynet.text,
            post.text
        )
        self.assertEqual(
            post_skynet.group,
            post.group
        )

    def test_new_post_not_on_follow_page(self):
        """ Check if post is hidden if not following """
        # create skynet post
        post_skynet = Post.objects.create(
            text="Skynet test not displaying",
            author=self.author,
            group=self.testgroup
        )
        response = self.client.get(reverse("follow_index"))
        page = response.context["page"]
        elements = len(page)
        self.assertEqual(elements, 0)

    def test_logged_in_comment(self):
        """ Logged user can comment """
        response = self.client.post(
            reverse("add_comment", args=[self.post.author, self.post.pk]),
            {
                "text": "Commenting",
                "author": self.user
            },
            follow=True
        )
        # compare context to database
        comments = response.context["items"]
        comment = comments[0]
        db_comment = Comment.objects.latest("created")
        self.assertEqual(
            comment.text,
            db_comment.text
        )
        self.assertEqual(
            comment.author,
            db_comment.author
        )

    def test_logged_out_comment(self):
        """ Logged out can not comment """
        response = self.client_unauthorized.post(
            reverse("add_comment", args=[self.post.author, self.post.pk]),
            {
                "text": "Commenting"
            },
            follow=True
        )
        response = self.client.get(
            reverse("post_single", args=[self.post.author, self.post.pk])
        )
        # check there is no comment added
        items = response.context["items"]
        elements = len(items)
        self.assertEqual(elements, 0)
