"""billy_the_messenger URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path
from django.conf.urls.static import static
from billy_the_messenger import settings
from main import views
from django.conf.urls import handler404, handler500, handler400, handler403

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.IndexView.as_view(), name='index'),
    path('signup/', views.UserRegistrationView.as_view(), name='signup'),
    path('signin/', views.LoginPageView.as_view(), name='signin'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('user_profile/', views.user_profile_settings, name='userprofile'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('dialogs/', views.DialogsPageView.as_view(), name='dialogs_page'),
    path('tm_reg_phone/', views.TmAuthPhoneView.as_view(), name='tm_reg_phone'),
    path('tm_reg_code/', views.TmAuthCodeView.as_view(), name='tm_reg_code'),
    path('dialogs/send/', views.send_message, name='send_message'),
    path('dialogs/get_messages/', views.get_new_messages, name='get_new_messages'),
    path('dialogs/get_dialogs/', views.get_new_dialogs, name='get_dialogs'),
    path('vk_auth/', views.VkAuthView.as_view(), name='vk_auth'),
    path('tm_auth/', views.TmAuthPhoneView.as_view(), name='tm_auth'),
    path('recover_password/', views.reset_password, name='recover_password'),
    path('change_password/', views.change_password, name='change_password'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


handler403 = views.handler403
handler404 = views.handler404
handler500 = views.handler500
