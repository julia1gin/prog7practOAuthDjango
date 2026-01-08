# Практическая работа

## Гиниятуллина Юлия Сергеевна, ИВТ 2.2

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

### 4.1 Регистрация приложения в Google Cloud Console

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

### 4.2 Конфигурация Django settings.py

#### 4.2.1 Добавление приложений в INSTALLED_APPS

```python
INSTALLED_APPS = [
    ...
    "django.contrib.sites",          
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",  # Google провайдер
]
```

#### 4.2.2 Добавление middleware

```python
MIDDLEWARE = [
    ...
    'allauth.account.middleware.AccountMiddleware',  # Для allauth
]
```

#### 4.2.3 Настройка authentication backends

```python
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',      # Стандартная авторизация
    'allauth.account.auth_backends.AuthenticationBackend',  # OAuth
]
```

#### 4.2.4 Конфигурация django-allauth

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

### 4.3 Создание кастомного адаптера

Создан файл `polls/adapters.py` для обработки данных пользователя из Google

### 4.4 Настройка URL маршрутов

В `mysite/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    ...
    path('accounts/', include('allauth.urls')),  # Все маршруты allauth
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
]
```

### 4.5 Настройка сайта и OAuth приложения

#### Создание Google OAuth приложения в БД

Создание через Django Admin (`/admin/socialaccount/socialapp/`)

### 4.6 Создание шаблона login.html

Создан файл `templates/account/login.html`:

---

## 5. Скриншоты работы приложения

### 5.1 Страница входа с кнопкой Google OAuth

![Страница входа](/images/img.png)

**Описание:** Страница логина с двумя вариантами входа:
- Кнопка "Continue with Google" с официальным дизайном Google
- Традиционная форма входа с полями username/email и password
- Разделитель "or" между способами авторизации

---

### 5.2 Авторизация в Google

![Вход через Google](/images/img_1.png)

**Описание:** Пользователь нажимает на кнопку "Continue with Google" и происходит перенаправление на сервер авторизации Google.

---

### 5.3 Окно выбора Google аккаунта

![Выбор аккаунта Google](/images/img_2.png)

**Описание:** Стандартное окно Google для выбора аккаунта и разрешения доступа к данным профиля (email, имя). Пользователь видит:
- Логотип приложения
- Запрашиваемые разрешения (profile, email)
- Список доступных Google аккаунтов для входа

---

### 5.4 Успешный вход в систему

![Успешный вход](/images/img_3.png)

**Описание:** После успешной авторизации через Google:
- Пользователь автоматически залогинен
- В навигации отображается username пользователя
- Показано сообщение успешного входа
- Доступны опции для staff пользователей (Create Poll, Admin)
- Появилась кнопка "Logout"

---
