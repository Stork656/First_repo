import imaplib
import email
import requests
import time
import os
import csv
from email.header import decode_header
from email import policy
from bs4 import BeautifulSoup
import ssl

# Читаем настройки из переменных окружения
IMAP_server = os.getenv('IMAP_SERVER', 'localhost')
IMAP_port = int(os.getenv('IMAP_PORT', '143'))
USE_SSL = os.getenv('IMAP_USE_SSL', 'false').lower() == 'true'
email_user = os.getenv('EMAIL_USER', 'pc1@diplom.test')
email_passw = os.getenv('EMAIL_PASS', '123')
API_URL = os.getenv('API_URL', 'http://127.0.0.1:8000/predict')

new_data_path = os.getenv('DATA_PATH', '/app/data')
os.makedirs(new_data_path, exist_ok = True)
csv_file = os.path.join(new_data_path, 'emails.csv')

if not os.path.exists(csv_file):
    with open(csv_file, mode = 'w', newline = '', encoding = 'utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Тема', 'Отправитель', 'Получатель', 'Тело сообщения', 'Вложения', 'Спам'])

def decode_mime_words(s):
    if not s:
        return 'Отсутствует'
    decoded = decode_header(s)
    return ''.join([
        part.decode(charset or 'utf-8') if isinstance(part, bytes) else part
        for part, charset in decoded
    ])

def parse_msg_object(msg, spam_label):
    attachments = []
    if msg.is_multipart():
        for part in msg.walk():
            content_disposition = part.get('Content-Disposition', '')
            filename = part.get_filename() or 'Без имени'
            if 'attachment' in content_disposition or 'inline' in content_disposition:
                attachments.append(filename)

    html_part = msg.get_body(preferencelist = ('html'))
    html = BeautifulSoup(html_part.get_content(), 'html.parser').get_text() if html_part else 'Отсутствует'

    plain_part = msg.get_body(preferencelist = ('plain'))
    plain = plain_part.get_content() if plain_part else 'Отсутствует'

    body_text = ''
    if plain != 'Отсутствует':
        body_text += plain
    if html != 'Отсутствует':
        body_text += '\n' + html
    if not body_text.strip():
        body_text = '[Без текста]'

    return {
        'Тема': decode_mime_words(msg['Subject']),
        'Отправитель': decode_mime_words(msg['From']),
        'Получатель': decode_mime_words(msg['To']),
        'Тело сообщения': body_text.strip(),
        'Вложения': ", ".join(attachments) if attachments else 'Отсутствуют',
        'Спам': spam_label
    }

def save_email_data(parsed):
    try:
        with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                parsed['Тема'],
                parsed['Отправитель'],
                parsed['Получатель'],
                parsed['Тело сообщения'],
                parsed['Вложения'],
                parsed['Спам']
            ])
    except PermissionError:
        print('Не удалось сделать запись. Проверьте, закрыт ли файл?')

def check_emails():
    try:
        if USE_SSL:
            mail = imaplib.IMAP4_SSL(IMAP_server, IMAP_port)
        else:
            mail = imaplib.IMAP4(IMAP_server, IMAP_port)

        mail.login(email_user, email_passw)
        mail.select('INBOX')

        status, messages = mail.search(None, 'UNSEEN')

        if messages[0]:
            for num in messages[0].split():
                status, data = mail.fetch(num, '(RFC822)')
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email, policy = policy.default)

                parsed = parse_msg_object(msg, spam_label = 0)

                combined_text = (
                    f"{parsed['Тема']} "
                    f"{parsed['Отправитель']} "
                    f"{parsed['Получатель']} "
                    f"{parsed['Тело сообщения']} "
                    f"{parsed['Вложения']}"
                )

                try:
                    response = requests.post(API_URL, json = {"text": combined_text})
                    result = response.json().get('prediction', '').lower().strip()
                except Exception as e:
                    print('Ошибка запроса к API:', e)
                    result = 'Отсутствует'

                subject = parsed['Тема']
                sender = parsed['Отправитель']

                if result == 'spam':
                    print(f'Письмо "{subject}" от {sender} спам и будет удалено.')
                    mail.store(num, '+FLAGS', '\\Deleted')
                    parsed['Спам'] = 1
                    save_email_data(parsed)
                elif result == 'not spam':
                    print(f'Письмо "{subject}" от {sender} прошло проверку.')
                    parsed['Спам'] = 0
                    save_email_data(parsed)
                else:
                    print(f'Непонятный ответ от API: "{result}". Письмо не сохранено.')
        else:
            print('Нет входящих...')

        mail.expunge()
        mail.logout()

    except Exception as e:
        print(f'Ошибка при проверке писем: {e}')

def main():
    print("Запуск проверки почты. Нажмите Ctrl+C для остановки.")
    try:
        while True:
            check_emails()
            time.sleep(10)
    except KeyboardInterrupt:
        print("Остановка фильтра...")

if __name__ == "__main__":
    main()
