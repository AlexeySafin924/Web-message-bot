from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from main.forms import SignUpForm
from django.contrib.auth.forms import AuthenticationForm
from main.tm import send_message
from pyrogram.api import errors
from pyrogram import Client as tmClient


class TestSignInPage(TestCase):

    def setUp(self):
        u = User(username="testuser", first_name="Vasya", last_name="Pupkin", is_active=1)
        u.set_password('pass')
        u.save()
        self.client = Client()
        self.url = reverse("signin")

    def test_signin_page_downloaded(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_signin_page_title(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context['title'], 'Billy the Messenger')

    def test_signin_page_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'billy_the_messenger/signin.html')

# self.assertFormError(response, 'wrong_form', 'some_field', 'Some error.')


class TestSignUpPage(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse("signup")

    def test_signup_page_downloaded(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_signup_page_title(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context['title'], 'Billy the Messenger')

    def test_signup_page_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'billy_the_messenger/signup.html')

    def test_help_text(self):
        form = SignUpForm()
        self.assertEqual(form.fields['email'].help_text, 'Required. Inform a valid email address.')
        self.assertEqual(form.fields['username'].help_text,
                         'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.')
        self.assertEqual(form.fields['password1'].help_text,
                         '<ul><li>Your password can&#39;t be too similar to your other personal '
                         'information.</li><li>Your password must contain at least 8 characters.</li><li>'
                         'Your password can&#39;t be a commonly used password.</li><li>Your password can&#39;t '
                         'be entirely numeric.</li></ul>')
        self.assertEqual(form.fields['password2'].help_text, 'Enter the same password as before, for verification.')

    def test_signup_page_short_password(self):
        response = self.client.post(self.url, {'username': 'testing_user', 'email': 'test@mail.ru',
                                               'password1': 'pasS5!', 'password2': 'pasS5!'})
        f = SignUpForm(response.wsgi_request.POST)
        array = f  # написать где хранятся ошибки
        flag = False
        for i in array:
            if array[i] == 'This password is too short. It must contain at least 8 characters.':
                flag = True
        self.assertTrue(flag)

    def test_signup_page_like_email_password(self):
        response = self.client.post(self.url, {'username': 'testing_user', 'email': 'testingtest@mail.ru',
                                               'password1': 'testingtest', 'password2': 'testingtest'})
        f = SignUpForm(response.wsgi_request.POST)
        array = f  # написать где хранятся ошибки
        flag = False
        for i in array:
            if array[i] == 'The password is too similar to the email address.':
                flag = True
        self.assertTrue(flag)

    def test_signup_page_like_username_password(self):
        response = self.client.post(self.url, {'username': 'testing_user', 'email': 'testingtest@mail.ru',
                                               'password1': 'testing_user', 'password2': 'testing_user'})
        f = SignUpForm(response.wsgi_request.POST)
        array = f  # написать где хранятся ошибки
        flag = False
        for i in array:
            if array[i] == 'The password is too similar to the username.':
                flag = True
        self.assertTrue(flag)

    def test_signup_page_numeral_password(self):
        response = self.client.post(self.url, {'username': 'testing_user', 'email': 'testingtest@mail.ru',
                                               'password1': '123456789', 'password2': '123456789'})
        f = SignUpForm(response.wsgi_request.POST)
        array = f  # написать где хранятся ошибки
        flag = False
        for i in array:
            if array[i] == 'This password is entirely numeric.':
                flag = True
        self.assertTrue(flag)

    def test_signup_page_not_same_password(self):
        response = self.client.post(self.url, {'username': 'testing_user', 'email': 'testingtest@mail.ru',
                                               'password1': 'qwerty12345', 'password2': 'qwerty1234'})
        f = SignUpForm(response.wsgi_request.POST)
        array = f  # написать где хранятся ошибки
        flag = False
        for i in array:
            if array[i] == "The two password fields didn't match.":
                flag = True
        self.assertTrue(flag)

    def test_signup_page_not_valid_username(self):
        response = self.client.post(self.url, {'username': 'testing user', 'email': 'testingtest@mail.ru',
                                               'password1': 'qwerty12345', 'password2': 'qwerty12345'})
        f = SignUpForm(response.wsgi_request.POST)
        array = f  # написать где хранятся ошибки
        flag = False
        for i in array:
            if array[i] == "Enter a valid username. This value may contain only " \
                           "letters, numbers, and @/./+/-/_ characters.":
                flag = True
        self.assertTrue(flag)


class TestSendingMsgsTM(TestCase):
    def setUp(self):
        client = tmClient("/tm_sessions/79609856120_session")
        client.start()

    def test_wrong_target(self):
        self.assertRaisers(errors.BadRequest, send_message, self.client.session, "123456789test", "testtesttest")

    def test_client_stopped(self):
        self.client.stop()
        self.assertRaisers(errors.Unauthorized, send_message, self.client.session, "shaponi", "testtesttest")
        self.client.start()

    def test_max_length(self):
        self.assertRaisers(errors.BadRequest, send_message, self.client.session, "shaponi", "a" * 5000)



