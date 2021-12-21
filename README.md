# hw05_final (YaTube)

### Описание
Данный учебный проект реализует импровизированную социальную сеть YaTube, позволяющую:
- Регистрироваться и аутентифицироваться пользователям
- Размещать посты с картинками или без
- Добавлять посты в группы
- Комментировать посты
- Оформлять подписки на различных авторов

### Запуск проекта в dev-режиме (Windows)

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/khalaimovda/hw05_final.git
```

```
cd hw05_final
```

Cоздать и активировать виртуальное окружение:

```
python -m venv env
```

```
source env/Scripts/activate
```

Установить зависимости из файла requirements.txt:

```
python -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Перейти в директорию основного приложения:

```
cd hw05_final
```

Выполнить миграции:

```
python manage.py migrate
```

Запустить проект:

```
python manage.py runserver
```

### Авторы

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Дмитрий Халаимов
