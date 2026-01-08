from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.contrib.auth.models import User


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Кастомный адаптер для обработки социальной аутентификации через Google
    """

    def pre_social_login(self, request, sociallogin):
        """
        Вызывается перед входом через социальную сеть.
        Связываем существующего пользователя с Google аккаунтом, если email совпадает.
        """
        # Если пользователь уже существует (уже вошел ранее)
        if sociallogin.is_existing:
            return

        # Если это первый вход через Google
        if sociallogin.account.provider == 'google':
            # Получаем email из данных Google
            data = sociallogin.account.extra_data
            email = data.get('email', '')

            if email:
                # Проверяем, существует ли пользователь с таким email
                try:
                    user = User.objects.get(email=email)
                    # Связываем существующего пользователя с Google аккаунтом
                    sociallogin.connect(request, user)
                    messages.info(
                        request,
                        'Your Google account has been connected to your existing account.'
                    )
                except User.DoesNotExist:
                    # Новый пользователь - будет создан автоматически
                    pass

    def save_user(self, request, sociallogin, form=None):
        """
        Сохранение пользователя после входа через Google.
        Извлекаем дополнительные данные из Google аккаунта.
        """
        user = super().save_user(request, sociallogin, form)

        # Получаем дополнительные данные из Google
        if sociallogin.account.provider == 'google':
            data = sociallogin.account.extra_data

            # Сохраняем имя и фамилию, если они есть
            if 'given_name' in data and not user.first_name:
                user.first_name = data['given_name']
            if 'family_name' in data and not user.last_name:
                user.last_name = data['family_name']

            user.save()

            messages.success(
                request,
                f'Welcome, {user.username}! You have successfully signed in with Google.'
            )

        return user

    def is_auto_signup_allowed(self, request, sociallogin):
        """
        Определяет, разрешена ли автоматическая регистрация.
        Возвращаем True для Google OAuth.
        """
        return sociallogin.account.provider == 'google'

    def populate_user(self, request, sociallogin, data):
        """
        Заполнение данных пользователя из социальной сети.
        Генерируем username из email, если он не указан.
        """
        user = super().populate_user(request, sociallogin, data)

        # Генерируем username из email, если не указан
        if not user.username:
            email = data.get('email', '')
            if email:
                # Берем часть до @ из email
                username_base = email.split('@')[0]

                # Убираем специальные символы
                username_base = ''.join(c for c in username_base if c.isalnum() or c == '_')

                # Проверяем уникальность и добавляем цифры при необходимости
                username = username_base
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{username_base}{counter}"
                    counter += 1

                user.username = username

        return user