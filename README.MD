# Инструкция по созданию и запуску Docker-контейнера с Flask-приложением

---
## 1. Запуск контейнера Ubuntu с пробросом порта 2266

```bash
sudo docker run -d --name vk_notification --net bridge -p 2266:2266 -i -t ubuntu /bin/bash
```

---
## 2. Подключение к контейнеру

```bash
sudo docker exec -it vk_notification /bin/bash
```

---
## 3. Обновление пакетов и установка необходимых инструментов

```bash
apt update
apt install -y nano python3-pip python3.12-venv
```

---
## 4. Создание и активация виртуального окружения Python 3.12

```bash
python3.12 -m venv venv
source venv/bin/activate
```

---
## 5. Установка необходимых Python-библиотек в виртуальном окружении

```bash
pip install Flask requests
```

---
## 6. Добавление вашего скрипта `app.py` в контейнер

```bash
nano app.py
```

Вставьте содержимое файла [app.py](app.py)

---
## 7. Добавление файла `requirements.txt` в контейнер

```bash
nano requirements.txt
```
Вставьте содержимое файла [requirements.txt](requirements.txt)

---
## 7. Запуск скрипта в контейнере

```bash
python3 app.py
```


## 8. Остановка скрипта для корректировок

Найдите PID процесса (в выводе искать по имени файла app.py): 

```bash
ps aux | grep python
```

Завершите процесс:

```bash
kill <PID>
```