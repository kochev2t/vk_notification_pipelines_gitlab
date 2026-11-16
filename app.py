#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
import requests
import time
import hashlib
import logging
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# =============================================================================
# 🔑 НАСТРОЙКИ
# =============================================================================

VK_ACCESS_TOKEN = '***'.strip()
VK_API_VERSION = '5.199'

REPO_CHAT_MAP = {
    'DEVELOP': 2000000006,
    'DEFAULT': 2000000011,
}

EMOJI = {
    'push': '\U0001F419',
    'merge': '\U0001F500',
    'build_ok': '\u2705',
    'build_fail': '\u274C',
    'build_cancel': '\U0001F92F',
    'build_run': '\U0001F3D7️',
    'user': '\U0001F464',
    'star': '\U0001F929',
    'branch': '\U0001F33F',
    'commit': '\U0001F4DD',
    'warning': '\u26A0️',
    'info': '\u2139️',
    'clock': '\U0001F550',
    'joy': '\U0001F973',
    'cry': '\U0001F62D',
    'evil': '\U0001F92C',
    'scull': '\U0001F480',
    'speak': '\U0001F4AD'
}

# =============================================================================
# 🎨 ФУНКЦИИ ФОРМАТИРОВАНИЯ (БЕЗ ССЫЛОК)
# =============================================================================

def generate_random_id() -> int:
    return int(hashlib.md5(f"{time.time()}{time.time_ns()}".encode()).hexdigest()[:8], 16) & 0xFFFFFFFF

def format_repo_name(name: str) -> str:
    """Форматирует название репозитория (без ссылки)"""
    return f"📁 `{name}`"

def format_author(author: str) -> str:
    """Форматирует имя автора"""
    return f"*{author}*"

def truncate_text(text: str, max_length: int = 70) -> str:
    """Обрезает длинный текст с многоточием"""
    if not text:
        return "без сообщения"
    text = text.split('\n')[0].strip()
    if len(text) > max_length:
        return text[:max_length-3] + "..."
    return text

def format_commit_hash(commit_hash: str) -> str:
    """Форматирует хэш коммита (без ссылки)"""
    if not commit_hash:
        return ""
    short_hash = commit_hash[:8]
    return f"`#{short_hash}`"

def get_time_ago(timestamp: str = None) -> str:
    """Возвращает время в читаемом формате"""
    if not timestamp:
        return datetime.now().strftime("%d.%m %H:%M")
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%d.%m %H:%M")
    except:
        return datetime.now().strftime("%d.%m %H:%M")

# =============================================================================
# 📤 ОТПРАВКА В VK
# =============================================================================

def send_to_vk_chat(peer_id: int, message: str) -> bool:
    url = "https://api.vk.com/method/messages.send"

    params = {
        "access_token": VK_ACCESS_TOKEN,
        "v": VK_API_VERSION,
        "peer_id": peer_id,
        "message": message,
        "random_id": generate_random_id(),
    }

    try:
        response = requests.post(url, data=params, timeout=15)
        result = response.json()

        if "response" in result:
            logging.info(f"✅ Сообщение отправлено в чат {peer_id}")
            return True
        elif "error" in result:
            err = result["error"]
            logging.error(f"❌ VK Error {err.get('error_code')}: {err.get('error_msg')}")
            return False
        else:
            logging.error(f"❌ Неожиданный ответ: {result}")
            return False

    except Exception as e:
        logging.error(f"❌ Ошибка запроса: {e}")
        return False

def get_target_peer_id(description: str) -> int:
    if not description:
        return REPO_CHAT_MAP['DEFAULT']

    desc_stripped = description.lstrip().upper()

    for prefix, peer_id in REPO_CHAT_MAP.items():
        if prefix == 'DEFAULT':
            continue
        if desc_stripped.startswith(prefix.upper()):
            logging.info(f"🎯 Найдено совпадение '{prefix}' → чат {peer_id}")
            return peer_id

    return REPO_CHAT_MAP['DEFAULT']

# =============================================================================
# 🎨 ФОРМАТИРОВАНИЕ СООБЩЕНИЙ (БЕЗ ССЫЛОК)
# =============================================================================

def format_push_message(data: dict) -> str:
    """Форматирование Push-события (компактный формат с разделителями)"""
    repo = data.get('repository', {}).get('name', 'unknown')
    ref = data.get('ref', 'refs/heads/master').split('/')[-1]
    commits = data.get('commits', [])
    
    if not commits:
        logging.info("Push без коммитов — пропускаем")
        return None
    
    # Заголовок
    lines = [f"В проект {repo}:{ref} внесены изменения:"]
    
    # Коммиты
    for commit in commits:
        author = commit.get('author', {}).get('name', 'Unknown')
        message = commit.get('message', 'без сообщения').strip()
        
        # Разделитель перед коммитом
        lines.append("")
        lines.append("***")
        lines.append(f"{EMOJI['speak']} {author}:{message}")
    
    # Подвал
    lines.append("")
    lines.append("***")
    lines.append(f"Ну хоть кто-то работает! {EMOJI['star']}")
    
    return "\n".join(lines)

def format_merge_request_message(data: dict) -> str:
    """Форматирование Merge Request (простой формат)"""
    repo = data.get('repository', {}).get('name', 'unknown')
    attrs = data.get('object_attributes', {})
    user = data.get('user', {}).get('name', 'Unknown')
    
    action = attrs.get('action', 'unknown')
    title = attrs.get('title', 'без названия')
    source = attrs.get('source_branch', 'unknown')
    target = attrs.get('target_branch', 'unknown')
    
    # ✅ ФИЛЬТР: Пропускаем только обновления и одобрения
    if action in ['update', 'approved', 'unapproved', 'reopened']:
        logging.info(f"🚫 Пропускаем промежуточное действие MR: {action}")
        return None
    
    # ✅ Определяем текст действия
    if action == 'open':
        action_text = "OPENED"
    elif action == 'merge':
        action_text = "MERGED"
    elif action == 'close':
        action_text = "CLOSED"
    else:
        action_text = action.upper()
    
    # ✅ Формируем сообщение
    message = (
        f"{EMOJI['scull']} {user} {action_text} merge request {title} "
        f"из {source} в {target} в проекте {repo}."
    )
    
    return message


def format_build_message(data: dict) -> str:
    """Форматирование Build/Pipeline (простой формат, только успех/ошибка)"""
    repo = data.get('repository', {}).get('name', 'unknown')
    
    status = data.get('build_status') or data.get('object_attributes', {}).get('status', 'unknown')
    
    # ✅ ФИЛЬТР: Пропускаем промежуточные статусы
    if status in ['running', 'pending', 'scheduled', 'waiting_for_resource', 'preparing', 'created']:
        logging.info(f"🚫 Пропускаем промежуточный статус сборки: {status}")
        return None
    
    name = data.get('build_name') or data.get('object_attributes', {}).get('name', 'build')
    
    # ✅ Форматируем по статусу
    if status == 'success':
        message = f"✅ В проекте {repo} задание {name} выполнилось успешно. {EMOJI['joy']}"
    elif status == 'failed':
        message = f"❌ В проект {repo} произошла ошибка.\nПри выполнении задания {name}. {EMOJI['cry']}"
    elif status == 'canceled':
        message = f"⚠️ В проекте {repo} было отменено задание {name}. {EMOJI['cry']}\nЗачем ты так? {EMOJI['evil']}"
    else:
        message = f"ℹ️ В проекте {repo} статус задания {name}: {status}"
    
    return message

# =============================================================================
# 📥 WEBHOOK ОБРАБОТЧИК
# =============================================================================

@app.route('/gitlab-webhook-vk', methods=['POST'])
def gitlab_webhook():
    message = ''
    data = request.get_json()

    if not data:
        logging.warning("Пустой JSON")
        return jsonify({"error": "No JSON"}), 400

    object_kind = data.get('object_kind', 'unknown')
    repo = data.get('repository', {}).get('name', 'unknown')
    description = data.get('repository', {}).get('description', '')

    logging.info(f"📨 Получено событие: {object_kind} | {repo} | desc: '{description}'")

    # === PUSH EVENT (всегда отправляем) ===
    if object_kind == 'push':
        commits = data.get('commits', [])
        if commits:
            message = format_push_message(data)
        else:
            logging.info("Push без коммитов — пропускаем")
            return jsonify({"status": "ignored", "reason": "no commits"}), 200

    # === MERGE REQUEST (только завершённые) ===
    elif object_kind == 'merge_request':
        message = format_merge_request_message(data)
        if message is None:  # ✅ Пропущено из-за фильтра
            return jsonify({"status": "ignored", "reason": "intermediate MR action"}), 200

    # === BUILD / PIPELINE (только успех/ошибка) ===
    elif object_kind in ['build', 'pipeline']:
        message = format_build_message(data)
        if message is None:  # ✅ Пропущено из-за фильтра
            return jsonify({"status": "ignored", "reason": "intermediate build status"}), 200

    else:
        logging.info(f"Неподдерживаемое событие: {object_kind}")
        return jsonify({"status": "ignored", "event": object_kind}), 200

    # Отправка в VK
    if message:
        target_peer_id = get_target_peer_id(description)
        success = send_to_vk_chat(target_peer_id, message)

        if not success:
            logging.error(f"Не удалось отправить в чат {target_peer_id}")
            return jsonify({
                "status": "sent_but_vk_error",
                "peer_id": target_peer_id
            }), 200

    return jsonify({
        "status": "ok",
        "event": object_kind,
        "repository": repo,
        "sent_to_peer": target_peer_id if message else None
    }), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "service": "gitlab-vk-webhook",
        "vk_configured": bool(VK_ACCESS_TOKEN and 'XXXX' not in VK_ACCESS_TOKEN),
        "chat_map": {k: v for k, v in REPO_CHAT_MAP.items() if k != 'DEFAULT'}
    }), 200

@app.route('/test', methods=['GET'])
def test_vk():
    msg = f"{EMOJI['star']}  *ТЕСТОВОЕ СООБЩЕНИЕ*\n{'─' * 40}\n\nЕсли вы видите это — всё работает!\n\n{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
    success = send_to_vk_chat(REPO_CHAT_MAP['DEFAULT'], msg)
    return jsonify({
        "status": "ok" if success else "error",
        "peer_id": REPO_CHAT_MAP['DEFAULT']
    }), 200 if success else 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2266, debug=False, threaded=True)