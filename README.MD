# VK Notification — запуск в Docker

Проект запускается в Docker-контейнере с Flask-приложением.
Порт `2266` внутри контейнера проброшен на порт `2266` хоста.

## Структура проекта

```text
vk_notification/
├── Dockerfile
├── docker-compose.yml
├── app.py
├── requirements.txt
└── README.md
```

## Требования

На сервере должны быть установлены:

- Docker
- Docker Compose

Проверить установку:

```bash
docker --version
docker compose version
```

## Подготовка файлов

В папке проекта должны находиться:

- `app.py` — код Flask-приложения
- `requirements.txt` — список Python-зависимостей
- `Dockerfile` — инструкция сборки образа
- `docker-compose.yml` — конфигурация запуска контейнера

Пример `requirements.txt`:

```text
Flask
requests
```

## Сборка и запуск

Перейдите в папку проекта:

```bash
cd vk_notification
```

Соберите образ и запустите контейнер в фоновом режиме:

```bash
sudo docker compose up -d --build
```

Команда:

- соберёт Docker-образ;
- создаст контейнер `vk_notification`;
- запустит `app.py`;
- оставит контейнер работать в фоне.

`--build` заставляет Docker пересобрать образ перед запуском, а `-d` запускает контейнер в detached-режиме. [11]

## Проверка работы

Посмотреть список запущенных контейнеров:

```bash
sudo docker compose ps
```

Посмотреть логи приложения:

```bash
sudo docker compose logs -f
```

Чтобы выйти из просмотра логов, нажмите `Ctrl + C`.
Это не остановит контейнер.

## Установка токена после запуска

После запуска контейнера необходимо зайти внутрь него и задать переменную окружения с токеном VK:

```bash
sudo docker compose exec vk_notification bash
```

Внутри контейнера выполните:

```bash
export VK_ACCESS_TOKEN='ваш_токен'
```

Замените `ваш_токен` на реальный access token VK.

Проверить, что переменная установлена:

```bash
echo $VK_ACCESS_TOKEN
```

После этого запустите приложение:

```bash
python3 app.py
```

Чтобы выйти из контейнера, выполните:

```bash
exit
```

## Доступ к приложению

После успешного запуска приложение доступно по адресу:

```text
http://<IP_сервера>:2266
```

Например, на самом сервере:

```text
http://localhost:2266
```

Если приложение запущено на другом порту внутри `app.py`, отредактируйте проброс портов в `docker-compose.yml`.

## Перезапуск после изменений

Если вы изменили `app.py`, `requirements.txt` или `Dockerfile`, выполните:

```bash
sudo docker compose up -d --build
```

Docker пересоберёт образ и перезапустит контейнер с обновлённым кодом.

## Остановка

Остановить и удалить контейнер:

```bash
sudo docker compose down
```

Остановить контейнер, но сохранить его:

```bash
sudo docker compose stop
```

Запустить ранее остановленный контейнер:

```bash
sudo docker compose start
```

Перезапустить контейнер:

```bash
sudo docker compose restart
```

## Вход в контейнер

Если нужно зайти внутрь работающего контейнера:

```bash
sudo docker compose exec vk_notification bash
```

Выйти из контейнера:

```bash
exit
```

## Возможные проблемы

### Порт 2266 уже занят

Проверьте, что использует порт:

```bash
sudo lsof -i :2266
```

или:

```bash
sudo ss -ltnp | grep 2266
```

Если порт занят другим процессом, остановите его либо измените проброс порта в `docker-compose.yml`.

### Приложение недоступно снаружи

Убедитесь, что в `app.py` Flask запускается так:

```python
app.run(host="0.0.0.0", port=2266)
```

Адрес `127.0.0.1` внутри контейнера не позволит получить доступ к приложению с хоста или из сети.

### Нужно полностью пересобрать образ

```bash
sudo docker compose down
sudo docker compose build --no-cache
sudo docker compose up -d
```