from django.urls import path
from . import views

app_name = 'polls'
urlpatterns = [
    # ex: /polls/
    path("", views.IndexView.as_view(), name="index"),
    # ex: /polls/5/
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    # ex: /polls/5/results/
    path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
    # ex: /polls/5/vote/
    path("<int:question_id>/vote/", views.VoteView.as_view(), name="vote"),
    path("new/", views.PollNewView.as_view(), name="poll_new"),
    # ex: /polls/5/edit/
    path('<int:pk>/edit/', views.PollEditView.as_view(), name='poll_edit'),

    # Старые маршруты
    # /accounts/login/ для входа
    # /accounts/signup/ для регистрации
    # /accounts/logout/ для выхода

    # path("login", views.LoginView.as_view(), name="login"),
    # path("logout", views.LogoutView.as_view(), name="logout"),
    # path("register", views.AccountRegisterView.as_view(), name="register"),
    # path("activate/<uidb64>/<token>", views.AccountActivationView.as_view(), name="activate"),
]
