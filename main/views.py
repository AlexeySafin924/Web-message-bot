import re
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sitemaps.views import index
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, redirect, render_to_response
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm, AuthenticationForm
from django.contrib.auth import login, logout, update_session_auth_hash
from django.core.mail import send_mail
from django.template import RequestContext
from django.urls import reverse_lazy
from django.views.generic import TemplateView, FormView, RedirectView, CreateView, View
from main.models import Profile
from django.contrib.auth.decorators import login_required
from main.forms import RecoverForm, SignUpForm, UserProfileForm, TMPhoneForm, TMCodeForm, VkAuthForm
import main.tm as tm
import time
import main.vkontakte as vk
from django.http import JsonResponse
from string import ascii_letters, digits


# TODO: add login_required
class DialogsPageView(TemplateView):
    template_name = 'billy_the_messenger/dialog_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = Profile.objects.get(user=self.request.user)
        if user.has_vk:
            api = vk.get_api(user)
            dialogs = vk.get_dialogs(api)
            vk.get_updates(user)
        elif user.has_tm:
            client = tm.get_client(user)
            dialogs = tm.get_dialogs(client)
        else:
            # TODO: add redirect to error page
            pass
        context['dialogs'] = dialogs

        context['name'] = 'Иван Иванов'
        context['host'] = re.sub(r'^https?://', '', self.request.build_absolute_uri('/'))
        return context


class TmDialogsPageView(TemplateView):
    template_name = 'billy_the_messenger/tm_dialog_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = Profile.objects.get(user=self.request.user)
        client = tm.get_client(user)
        dialogs = tm.get_dialogs(client)

        with open('parsed_dialogs.txt', 'w') as file:
            file.write(str(dialogs))
        context['dialogs'] = dialogs

        context['name'] = 'Иван Иванов'
        context['host'] = re.sub(r'^https?://', '', self.request.build_absolute_uri('/'))
        return context


class IndexView(TemplateView):

    def get(self, request, *args, **kwargs):
        print(vk.user_sessions)
        return super(IndexView, self).get(request, *args, **kwargs)

    template_name = "billy_the_messenger/index.html"


class AboutView(TemplateView):
    template_name = "billy_the_messenger/about.html"


class LoginPageView(FormView):
    template_name = "billy_the_messenger/signin.html"
    form_class = AuthenticationForm
    success_url = "/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Billy the Messenger'
        return context

    def form_valid(self, form):
        login(self.request, form.get_user())
        return super(LoginPageView, self).form_valid(form)


class VkAuthView(FormView):
    template_name = 'billy_the_messenger/vk_auth.html'
    form_class = VkAuthForm

    def form_valid(self, form):
        login = self.request.POST['login']
        password = self.request.POST['password']
        user = Profile.objects.get(user=self.request.user)
        _ = vk.get_api(user, login, password, True)
        vk.set_update_handler(user)
        user.has_vk = True
        user.save()
        return redirect('index')


class TmAuthPhoneView(FormView):
    template_name = 'billy_the_messenger/tm_reg_phone.html'
    form_class = TMPhoneForm

    def form_valid(self, form):
        phone = form["phone"].value()
        A = tm.Timer(1, tm.auth, [phone])
        A.start()
        return redirect('tm_reg_code')


class TmAuthCodeView(FormView):
    template_name = 'billy_the_messenger/tm_reg_code.html'
    form_class = TMCodeForm

    def form_valid(self, form):
        with open("tm_reg_code.txt", 'w') as file:
            file.write(form["code"].value())
        return redirect('index')


class TmGetDialog(FormView):
    template_name = 'billy_the_messenger/tm_get_dialog.html'
    form_class = TMCodeForm

    def form_valid(self, form):
        tm.get_messages('tm_sessions/89164847949', form["code"].value())
        return redirect('index')


class LogoutView(RedirectView):
    url = "/"

    def get(self, request, *args, **kwargs):
        logout(request)
        return super(LogoutView, self).get(request, *args, **kwargs)


class UserRegistrationView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('index')
    template_name = "billy_the_messenger/signup.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Billy the Messenger'
        return context

    def form_valid(self, form, *args, **kwargs):
        self.object = form.save()
        login(self.request, self.object)
        profile = Profile(user=self.object)
        profile.save()
        print('---------------------')
        print(form.fields['password1'].help_text)
        return HttpResponseRedirect(self.get_success_url())


def reset_password(request):
    context = {}
    if request.method == 'POST':
        form = RecoverForm(request.POST)
        if form.is_valid():
            name = form.data['username']
            u = User.objects.filter(username=name).first()
            if u is not None:
                new_password = User.objects.make_random_password(length=10, allowed_chars=ascii_letters + digits)
                u.set_password(new_password)
                u.save()
                message = 'Hi! Your new password is: ' + new_password
                mail = u.email
                send_mail('New Password', message, 'from@example.com', [mail])
                messages.info(request, 'Новый пароль отправлен на почту')
                return redirect("index")
            else:
                messages.warning(request, 'Smth got wrong with user. Go to <a href="/">main</a>.')
                return redirect("index")
        else:
            messages.warning(request, 'Форма заполнена неправильно')
            return redirect("index")
    else:
        form = RecoverForm()
        context['recover_form'] = form
    return render(request, 'billy_the_messenger/recover_password.html', context)


def change_password(request):
    context = {}
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успешно сменён.')
            return redirect("userprofile")
        else:
            messages.warning(request, 'Неправильная форма.')
            return redirect("userprofile")


@login_required
def user_profile_settings(request):
    context = {}
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            p = Profile.objects.filter(user=request.user).first()
            has_vk = form.data.get("has_vk")
            has_tm = form.data.get("has_tm")
            use_bot = form.data.get("use_bot")
            theme = form.data.get("theme")
            if has_vk:
                p.has_vk = True
            else:
                p.has_vk = False
            if has_tm:
                p.has_tm = True
            else:
                p.has_tm = False
            if use_bot:
                p.use_bot = True
            if theme:
                p.theme = theme
            if form.data["img"]:
                p.avatar = form.data["img"]
            p.save()
            messages.info(request, 'Настройки успешно применены')
            return redirect("userprofile")
        else:
            messages.warning(request, 'Форма заполнена неправильно')
            return redirect("userprofile")
    else:
        profile = Profile.objects.filter(user=request.user).first()
        form = UserProfileForm(instance=profile)
        context['user_profile_form'] = form
        context['avatar'] = '/static/images/avatars/default.png/'
        context['email'] = request.user.email
        context['nickname'] = request.user.username
        context['password_form'] = PasswordChangeForm(request.user)
        context['has_vk'] = profile.has_vk
        context['has_tm'] = profile.has_tm

    return render(request, 'billy_the_messenger/user_profile.html', context)


def set_status(request, status, mode):
    request.session[status] = mode
    request.session.set_expiry(86400)


def set_offline(db, id):
    t = db.objects.filter(user=id)
    t.is_online = False
    t.save()


def tm_auth_phone(request):
    context = {}
    if request.method == 'POST':
        form = TMPhoneForm(request.POST)
        if form.is_valid():
            phone = form.data['phone']
            tm.auth(phone)
            return redirect('/')
        else:
            return HttpResponse('Форма заполнена неправильно')
    else:
        form = TMPhoneForm()
        context['tm_mess_form'] = form
    return render(request, index, context)


class JsonResponseMixin(LoginRequiredMixin):
    """
    A mixin that can be used to render a JSON response.
    """

    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        return JsonResponse(
            self.get_data(context),
            **response_kwargs
        )

    def get_data(self, context):
        """
        Returns an object that will be serialized as JSON by json.dumps().
        """
        # Note: This is *EXTREMELY* naive; in reality, you'll need
        # to do much more complex handling to ensure that arbitrary
        # objects -- such as Django model instances or querysets
        # -- can be serialized as JSON.
        return context


#
#
# ## Used to deliver new messages
# #
# # This class serves the AJAX for getting new messages based on the oldest message timestamp
# class AjaxLoadMoreMessages(JsonResponseMixin, LoginRequiredMixin, TemplateView):
#     ## True on raise_exception will lead to 403 error if client is not authenticated
#     #
#     # We do not need to redirect to sign in page as this view is designed to be used by AJAX
#     raise_exception = True
#
#     def render_to_response(self, context, **response_kwargs):
#         return self.render_to_json_response(context, **response_kwargs)
#
#
#     def get_data(self, request, **kwargs):
#         # timestamp = int(request.GET)
#         # messages = getNewMessages(timestamp)
#         messages = {
#             'text': 'Testing AJAX auto load',
#             'time': 1523783393,
#             'mine': False,
#         }
#         return messages
#
#     def get(self, request, *args, **kwargs):
#         return self.render_to_response(request)

def send_message(request):
    mode = request.GET['mode']
    target = request.GET['target']
    text = request.GET['text']
    fwd_messages = request.GET.get('fwd_messages', [])
    from_id = request.GET.get('from_id', None)
    user = Profile.objects.get(user=request.user)
    if mode == 'tm':
        client = tm.get_client(user)
        if fwd_messages:
            tm.forward_messages(client, target, from_id, fwd_messages)
        tm.send_message(client, target, text)
    elif mode == 'vk':
        api = vk.get_api(user)
        vk.send_message(api, target, text, fwd_messages)
    return JsonResponse(safe=False)


def get_new_messages(request):
    mode = request.GET['mode']
    id = int(request.GET['id'])
    limit = int(request.GET['limit'])
    offset = int(request.GET['offset'])
    is_chat = True if request.GET['is_chat'] == 'True' else False

    user = Profile.objects.get(user=request.user)

    if mode == 'tm':
        client = tm.get_client(user)
        messages = tm.get_messages(client, id, offset, limit)
    else:
        api = vk.get_api(user)
        messages = vk.get_messages(api, id, offset, limit, is_chat)

    if offset == 0:
        messages['messages'] = messages['messages'][::-1]

    return JsonResponse(messages, safe=False)


def get_new_dialogs(request):
    mode = request.GET.get('mode')
    if mode is None:
        return JsonResponse(dict(error='No mode was specified'), safe=False)

    user = Profile.objects.get(user=request.user)
    if mode == 'tm':
        client = tm.get_client(user)
        dialogs = tm.get_dialogs(client)
    elif mode == 'vk':
        api = vk.get_api(user)
        dialogs = vk.get_dialogs(api)
    else:
        return JsonResponse(dict(error='Invalid mode was specified'), safe=False)

    return JsonResponse(dict(dialogs=dialogs), safe=False)


def handler403(request):
    return render(request, 'error_pages/403.html', status=403)


def handler404(request):
    return render(request, 'error_pages/404.html', status=404)


def handler500(request):
    return render(request, 'error_pages/500.html', status=500)
