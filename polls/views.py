import random
import logging

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import View, generic
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import redirect_to_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from django.http import HttpResponse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.models import User

from .forms import NewUserForm

from .models import Choice, Question
from .forms import QuestionForm

SLOGANS = [
    "Polls or Trolls: Without your choice, beware the gremlins' voice!",
    "Polls or Spooks: Don't let phantoms choose your folks!",
    "Polls or Ghouls: Vote or let the underworld fool!",
    "Polls or Wraiths: Make a choice or invite spectral straits!",
    "Polls or Shadows: Without your say, darkness grows!",
    "Polls or Beasts: Choose wisely, or unleash monstrous feasts!",
    "Polls or Nightmares: Cast your vote, or fall into horror's lairs!",
    "Polls or Ghosts: Decide or invite the haunted costs!",
    "Polls or Fiends: Without your voice, chaos reigns!",
    "Polls or Vampires: Your choice could calm the nocturnal pyres!",
    "Polls or Goblins: Without a vote, mischief unfolds in!",
    "Polls or Crows: Cast your choice or let dark omens rise!",
    "Polls or Skeletons: A vote unsaid releases bone-ridden threats!",
    "Polls or Serpents: Fail to choose, and risk subterranean events!",
    "Polls or Abyss: A silent electorate summons the darkness!"
]


class PollsBaseView(View):
    slogans = SLOGANS

    def get_slogan(self):
        return random.choice(self.slogans)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['slogan'] = self.get_slogan()
        return context


class IndexView(PollsBaseView, generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """Return the last five published questions (not including those set to be
        published in the future).
        """
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[
               :5
               ]


class DetailView(PollsBaseView, generic.DetailView):
    model = Question
    template_name = "polls/detail.html"

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(PollsBaseView, generic.DetailView):
    model = Question
    template_name = "polls/results.html"


class VoteView(PollsBaseView, LoginRequiredMixin, View):
    """
    Vote view теперь требует авторизации!
    Если пользователь не авторизован, будет перенаправлен на /accounts/login/
    """
    login_url = '/accounts/login/'  # Используем allauth URL

    def post(self, request, question_id):
        question = get_object_or_404(Question, pk=question_id)
        try:
            selected_choice = question.choice_set.get(pk=request.POST["choice"])
        except (KeyError, Choice.DoesNotExist):
            # Redisplay the question voting form.
            return render(
                request,
                "polls/detail.html",
                {
                    "slogan": self.get_slogan(),
                    "question": question,
                    "error_message": "You didn't select a choice.",
                },
            )
        else:
            selected_choice.votes += 1
            selected_choice.save()
            messages.success(request, f"Your vote for '{selected_choice.choice_text}' has been recorded!")
            # Always return an HttpResponseRedirect after successfully dealing
            # with POST data. This prevents data from being posted twice if a
            # user hits the Back button.
            return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))


class UserIsStaffMixin(UserPassesTestMixin):
    login_url = "/accounts/login/"  # Изменено на allauth URL
    redirect_field_name = "next"
    raise_exception = False

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect_to_login(self.request.get_full_path(), self.login_url, self.redirect_field_name)


class PollNewView(PollsBaseView, UserIsStaffMixin, LoginRequiredMixin, View):

    def get(self, request):
        form = QuestionForm()
        return render(
            request,
            'polls/poll_new_edit.html',
            {
                'form': form,
                "slogan": self.get_slogan(),
            }
        )

    def post(self, request):
        form = QuestionForm(request.POST)
        if form.is_valid():
            poll = form.save(commit=False)
            poll.save()
            messages.success(request, "Poll created successfully!")
            return redirect('polls:detail', pk=poll.pk)
        return render(
            request,
            'polls/poll_new_edit.html',
            {
                'form': form,
                "slogan": self.get_slogan(),
            }
        )


class PollEditView(PollsBaseView, UserIsStaffMixin, LoginRequiredMixin, View):

    def get(self, request, pk):
        poll = get_object_or_404(Question, pk=pk)
        form = QuestionForm(instance=poll)
        return render(
            request, 'polls/poll_new_edit.html', {
                "slogan": self.get_slogan(),
                'form': form
            }
        )

    def post(self, request, pk):
        poll = get_object_or_404(Question, pk=pk)
        form = QuestionForm(request.POST, instance=poll)
        if form.is_valid():
            poll = form.save(commit=False)
            poll.pub_date = timezone.now()
            poll.save()
            messages.success(request, "Poll updated successfully!")
            return redirect('polls:detail', pk=poll.pk)
        return render(
            request, 'polls/poll_new_edit.html', {
                "slogan": self.get_slogan(),
                'form': form
            }
        )

# ============================================
# СТАРЫЕ VIEWS ДЛЯ ВХОДА/РЕГИСТРАЦИИ
# Больше не используются, так как теперь используем django-allauth
# ============================================

# class LoginView(PollsBaseView, View):
#     logger = logging.getLogger(__name__)
#
#     def get(self, request):
#         form = AuthenticationForm()
#         return render(
#             request=request,
#             template_name="polls/login.html",
#             context={
#                 "form": form,
#                 "slogan": self.get_slogan(),
#             }
#         )
#
#     def post(self, request):
#         form = AuthenticationForm(request, data=request.POST)
#         if form.is_valid():
#             username = form.cleaned_data.get('username')
#             password = form.cleaned_data.get('password')
#             user = authenticate(username=username, password=password)
#             if user is not None:
#                 login(request, user)
#                 messages.info(request, f"You are now logged in as {username}.")
#                 next_url = self.request.GET.get('next')
#                 if next_url:
#                     return redirect(next_url)
#                 else:
#                     return redirect('polls:index')
#             else:
#                 messages.error(request, "Invalid username or password.")
#         else:
#             messages.error(request, "Invalid username or password.")
#
#         return render(
#             request=request,
#             template_name="polls/login.html",
#             context={
#                 "form": form,
#                 "slogan": self.get_slogan(),
#             }
#         )


# class LogoutView(View):
#     def get(self, request):
#         logout(request)
#         messages.info(request, "You have successfully logged out.")
#         return redirect("polls:index")


# class AccountRegisterView(View):
#     form_class = NewUserForm
#     template_name = "polls/register.html"
#
#     def get(self, request):
#         form = self.form_class()
#         return render(
#             request=request,
#             template_name=self.template_name,
#             context={
#                 "form": form,
#                 "slogan": self.get_slogan() if hasattr(self, 'get_slogan') else "",
#             }
#         )
#
#     def post(self, request):
#         form = self.form_class(request.POST)
#         if form.is_valid():
#             user = form.save(request)
#             messages.success(request,
#                              f"Registration successful. Please go to your '{user.email}' e-mail inbox messages to activate the account.")
#             return redirect("polls:index")
#
#         messages.error(request, "Unsuccessful registration. Invalid information.")
#         return render(
#             request=request,
#             template_name=self.template_name,
#             context={
#                 "form": form,
#                 "slogan": self.get_slogan() if hasattr(self, 'get_slogan') else "",
#             }
#         )


# class AccountActivationView(View):
#     def get(self, request, uidb64, token):
#         try:
#             uid = force_str(urlsafe_base64_decode(uidb64))
#             user = User.objects.get(pk=uid)
#         except:
#             user = None
#
#         if user is not None and default_token_generator.check_token(user, token):
#             user.is_active = True
#             user.save()
#             messages.success(request, "Account activated successfully!")
#             return redirect("polls:login")
#         else:
#             messages.error(request, "Activation link is invalid!")
#             return redirect("polls:index")