# Практическая работа
## Настройка OAuth 2.0 авторизации в Django приложении (Django + OAuth + Google)

---

## 1. Цель работы

Улучшите приложение для голосований из лабораторных работ и реализуйте вход на сайт этого приложения через
стандарт OAuth, при условии, что пользователь имеет учётную запись Google

---

## 2. Задачи

1. Установить и настроить библиотеку `django-allauth` для работы с OAuth 2.0
2. Зарегистрировать приложение в Google Cloud Console и получить OAuth credentials
3. Настроить Django для работы с Google OAuth провайдером
4. Создать кастомный адаптер для обработки данных пользователя из Google
5. Адаптировать шаблоны для отображения кнопки "Continue with Google"
6. Протестировать полный цикл авторизации через Google

---

## 3. OAuth 2.0

**OAuth 2.0** — это протокол авторизации, который позволяет пользователям предоставлять сторонним приложениям доступ к их ресурсам без передачи логина и пароля.

**Основные участники OAuth 2.0:**
- **Resource Owner** (Владелец ресурса) — пользователь
- **Client** (Клиент) — наше Django приложение
- **Authorization Server** (Сервер авторизации) — Google
- **Resource Server** (Сервер ресурсов) — API Google (профиль, email)


### Django-allauth

**django-allauth** — это комплексное решение для аутентификации в Django, поддерживающее:
- Регистрацию и вход пользователей
- Email верификацию
- Социальную аутентификацию (Google, GitHub, Facebook и др.)
- Управление аккаунтами

---

## 4. Ход выполнения работы

### 4.1 Установка зависимостей

Добавлены необходимые пакеты в `requirements.txt`:

```txt
Django==5.2.7
django-allauth==64.2.0
python-dotenv==1.1.1
crispy-bootstrap5==2025.6
django-crispy-forms==2.4
```

Установка:
```bash
pip install django-allauth python-dotenv
```

### 4.2 Регистрация приложения в Google Cloud Console

**Шаги:**

1. Переход на [Google Cloud Console](https://console.cloud.google.com/)
2. Создание нового проекта или выбор существующего
3. Включение **Google+ API** и **Google Identity API**
4. Создание **OAuth 2.0 Client ID** в разделе "Credentials"
5. Настройка OAuth consent screen:
   - Application name: "Polls Application"
   - User support email
   - Scopes: `profile`, `email`

6. Настройка **Authorized redirect URIs**:
   ```
   http://127.0.0.1:8000/accounts/google/login/callback/
   http://localhost:8000/accounts/google/login/callback/
   ```

7. Настройка **Authorized JavaScript origins**:
   ```
   http://127.0.0.1:8000
   http://localhost:8000
   ```

8. Получение **Client ID** и **Client Secret**

### 4.3 Конфигурация Django settings.py

#### 4.3.1 Добавление приложений в INSTALLED_APPS

```python
INSTALLED_APPS = [
    "polls.apps.PollsConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    
    # Crispy forms
    "crispy_forms",
    "crispy_bootstrap5",
    
    # Django-allauth (для OAuth)
    "django.contrib.sites",          
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",  # Google провайдер
]
```

#### 4.3.2 Добавление middleware

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Для allauth
]
```

#### 4.3.3 Настройка authentication backends

```python
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',      # Стандартная авторизация
    'allauth.account.auth_backends.AuthenticationBackend',  # OAuth
]
```

#### 4.3.4 Конфигурация django-allauth

```python
# Site ID для django.contrib.sites
SITE_ID = 1

# Настройки аккаунта
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'  # Вход по username или email
ACCOUNT_EMAIL_VERIFICATION = 'optional'

# Перенаправления после входа/выхода
LOGIN_REDIRECT_URL = '/polls/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/polls/'

# Настройки социальной аутентификации
SOCIALACCOUNT_AUTO_SIGNUP = True      # Автоматическая регистрация
SOCIALACCOUNT_EMAIL_REQUIRED = True   # Email обязателен
SOCIALACCOUNT_QUERY_EMAIL = True      # Запрашивать email

# Кастомный адаптер
SOCIALACCOUNT_ADAPTER = 'polls.adapters.MySocialAccountAdapter'

# Настройки Google OAuth провайдера
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}
```


### 4.4 Создание кастомного адаптера

Создан файл `polls/adapters.py` для обработки данных пользователя из Google:

```python
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
        if sociallogin.is_existing:
            return

        if sociallogin.account.provider == 'google':
            data = sociallogin.account.extra_data
            email = data.get('email', '')

            if email:
                try:
                    user = User.objects.get(email=email)
                    sociallogin.connect(request, user)
                    messages.info(
                        request,
                        'Your Google account has been connected to your existing account.'
                    )
                except User.DoesNotExist:
                    pass

    def save_user(self, request, sociallogin, form=None):
        """
        Сохранение пользователя после входа через Google.
        Извлекаем дополнительные данные из Google аккаунта.
        """
        user = super().save_user(request, sociallogin, form)

        if sociallogin.account.provider == 'google':
            data = sociallogin.account.extra_data

            # Сохраняем имя и фамилию
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
        """
        return sociallogin.account.provider == 'google'

    def populate_user(self, request, sociallogin, data):
        """
        Заполнение данных пользователя из социальной сети.
        Генерируем уникальный username из email.
        """
        user = super().populate_user(request, sociallogin, data)

        if not user.username:
            email = data.get('email', '')
            if email:
                # Берем часть до @ из email
                username_base = email.split('@')[0]
                
                # Убираем специальные символы
                username_base = ''.join(
                    c for c in username_base if c.isalnum() or c == '_'
                )

                # Проверяем уникальность
                username = username_base
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{username_base}{counter}"
                    counter += 1

                user.username = username

        return user
```

**Основные функции адаптера:**
- `pre_social_login` — связывает Google аккаунт с существующим Django пользователем по email
- `save_user` — сохраняет имя и фамилию из Google профиля
- `populate_user` — генерирует уникальный username из email
- `is_auto_signup_allowed` — разрешает автоматическую регистрацию

### 4.5 Настройка URL маршрутов

В `mysite/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('polls/', include('polls.urls')),
    path('accounts/', include('allauth.urls')),  # Все маршруты allauth
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
]
```

**Важные URL от allauth:**
- `/accounts/login/` — страница входа
- `/accounts/signup/` — регистрация
- `/accounts/logout/` — выход
- `/accounts/google/login/` — начало OAuth процесса
- `/accounts/google/login/callback/` — callback после авторизации в Google

### 4.6 Применение миграций

```bash
python manage.py migrate
```

Создаются таблицы:
- `django_site` — для хранения информации о сайте
- `socialaccount_socialapp` — OAuth приложения (Google)
- `socialaccount_socialaccount` — связь пользователей с соц. сетями
- `socialaccount_socialtoken` — токены доступа

### 4.7 Настройка сайта и OAuth приложения

#### Создание Google OAuth приложения в БД

Создание через Django Admin (`/admin/socialaccount/socialapp/`)

### 4.8 Создание шаблона login.html

Создан файл `templates/account/login.html`:

**Ключевые элементы:**
- `{% load socialaccount %}` — загрузка тегов allauth
- `{% provider_login_url 'google' %}` — генерация URL для OAuth
- Кнопка с официальным стилем Google
- Разделитель "or" между OAuth и традиционной формой

### 4.9 Обновление базового шаблона

В `templates/base.html` добавлены стили для Google кнопки:

```css
.google-btn {
    background: #fff;
    border: 1px solid #dadce0;
    border-radius: 4px;
    color: #3c4043;
    font-family: 'Roboto',arial,sans-serif;
    padding: 10px 12px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
    text-decoration: none;
    width: 100%;
}

.google-btn:hover {
    background: #f8f9fa;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    transform: translateY(-1px);
}
```

Навигация обновлена для использования URL от allauth:

```html
{% if user.is_authenticated %}
    <li class="nav-item">
        <span class="nav-link text-info">👤 {{ user.username }}</span>
    </li>
    <li class="nav-item">
        <a class="nav-link" href="{% url 'account_logout' %}">🚪 Logout</a>
    </li>
{% else %}
    <li class="nav-item">
        <a class="nav-link" href="{% url 'account_login' %}">🔐 Login</a>
    </li>
    <li class="nav-item">
        <a class="nav-link" href="{% url 'account_signup' %}">📝 Register</a>
    </li>
{% endif %}
```

---

## 5. Тестирование

```bash
python manage.py runserver
```

### Сценарий 1: Новый пользователь (первый вход через Google)

**Шаги:**

1. Открыть `http://127.0.0.1:8000/accounts/login/`
2. Нажать кнопку **"Continue with Google"**
3. Перенаправление на страницу авторизации Google
4. Выбрать Google аккаунт
5. Разрешить доступ к профилю и email
6. Автоматическое перенаправление обратно на сайт
7. Создание нового пользователя в Django
8. Вход в систему и редирект на `/polls/`

**Ожидаемый результат:**
- ✅ Пользователь создан в базе данных
- ✅ Username сгенерирован из email (например, `johndoe` из `johndoe@gmail.com`)
- ✅ Email сохранен
- ✅ Имя и фамилия из Google профиля сохранены
- ✅ Отображается сообщение: "Welcome, johndoe! You have successfully signed in with Google."


### Сценарий 2: Существующий пользователь с таким же email

**Предусловие:** В базе уже есть пользователь с email `johndoe@gmail.com` (зарегистрирован через традиционную форму)

**Шаги:**

1. Открыть `/accounts/login/`
2. Нажать "Continue with Google"
3. Войти через Google с аккаунтом `johndoe@gmail.com`

**Ожидаемый результат:**
- ✅ Google аккаунт **связывается** с существующим пользователем
- ✅ Новый пользователь НЕ создается
- ✅ Вход выполняется под существующим аккаунтом
- ✅ Сообщение: "Your Google account has been connected to your existing account."

### Сценарий 3: Повторный вход через Google

**Шаги:**

1. Выйти из системы (`/accounts/logout/`)
2. Открыть `/accounts/login/`
3. Нажать "Continue with Google"

**Ожидаемый результат:**
- ✅ Быстрая авторизация (Google помнит выбор)
- ✅ Мгновенный вход без дополнительных подтверждений
- ✅ Редирект на `/polls/`

---

## 6. Скриншоты работы приложения

### 8.1 Главная страница приложения

![Главная страница](https://github.com/user-attachments/assets/18168710-73bb-4b79-9183-7619190fa2cb)

**Описание:** Главная страница приложения Polls с навигацией. Видны ссылки "Login" и "Register" для неавторизованных пользователей.

---

### 8.2 Страница входа с кнопкой Google OAuth

![Страница входа](https://github.com/user-attachments/assets/a46df223-c0d3-41b9-a476-0f4547c24bd6)

**Описание:** Страница логина с двумя вариантами входа:
- Кнопка "Continue with Google" с официальным дизайном Google
- Традиционная форма входа с полями username/email и password
- Разделитель "or" между способами авторизации

---

### 8.3 После клика на "Continue with Google"

![Вход через Google](https://github.com/user-attachments/assets/b8aeacc3-95da-40e4-b321-c96dfd3993d9)

**Описание:** Пользователь нажимает на кнопку "Continue with Google" и происходит перенаправление на сервер авторизации Google.

---

### 8.4 Окно выбора Google аккаунта

![Выбор аккаунта Google](https://github.com/user-attachments/assets/080158d8-1ef3-4f51-8dc7-d4935be9d34e)

**Описание:** Стандартное окно Google для выбора аккаунта и разрешения доступа к данным профиля (email, имя). Пользователь видит:
- Логотип приложения
- Запрашиваемые разрешения (profile, email)
- Список доступных Google аккаунтов для входа

---

### 8.5 Успешный вход в систему

![Успешный вход](https://github.com/user-attachments/assets/5a2489c8-55a5-44d7-ab64-2719fc801c4e)

**Описание:** После успешной авторизации через Google:
- Пользователь автоматически залогинен
- В навигации отображается username пользователя
- Показано сообщение успешного входа
- Доступны опции для staff пользователей (Create Poll, Admin)
- Появилась кнопка "Logout"

---

### 8.6 Страница выхода из системы

![Выход из системы](https://github.com/user-attachments/assets/eeb0fd9f-b842-4659-8ba5-33f6a5196f41)

**Описание:** Страница подтверждения выхода из системы с кнопкой "Sign Out". После выхода пользователь возвращается на главную страницу как неавторизованный.

---




