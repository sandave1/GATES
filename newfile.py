import requests
import time
from datetime import datetime, timedelta
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import threading

# Replace with your bot token
TOKEN = '6700824149:AAGjDy02xoE-IUK0u6McLeqmaOAWk_jb97Q'
URL = f'https://api.telegram.org/bot{TOKEN}/'
MAX_MESSAGE_LENGTH = 4096

# Lock for thread-safe operations on shared resources
lock = threading.Lock()

# Functions to interact with Telegram API
def get_updates(offset=None):
    url = URL + 'getUpdates'
    params = {'timeout': 50, 'offset': offset}
    response = requests.get(url, params=params)
    return response.json()

def send_message(chat_id, text):
    url = URL + 'sendMessage'
    params = {'chat_id': chat_id, 'text': text}
    requests.get(url, params=params)

def split_message(text):
    """Splits a long message into smaller parts to fit within Telegram's limits."""
    return [text[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(text), MAX_MESSAGE_LENGTH)]

# Functions to analyze websites
def analyze_site(url):
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    result = {
        'url': url, 'payment_gateways': [], 'captcha': False, 
        'cloudflare': False, 'graphql': False, 'platform': None, 
        'http_status': None, 'content_type': None, 'cookies': {}, 
        'error': None, 'country': None
    }

    try:
        response = requests.get(url, timeout=10)
        headers = response.headers
        content_type = headers.get('Content-Type', '')
        response_text = response.text
        cookies = response.cookies.get_dict()
        country = headers.get('CF-IPCountry', 'Unknown')

        # Extract HTTP version and status code with reason phrase
        http_version = 'HTTP/1.1' if response.raw.version == 11 else 'HTTP/1.0'
        status_code = response.status_code
        reason_phrase = response.reason
        http_status = f"{http_version} {status_code} {reason_phrase}"

        result.update({
            'payment_gateways': check_for_payment_gateways(headers, response_text, cookies),
            'cloudflare': check_for_cloudflare(response_text),
            'captcha': check_for_captcha(response_text),
            'graphql': check_for_graphql(response_text),
            'platform': check_for_platform(response_text),
            'http_status': http_status,
            'content_type': content_type,
            'cookies': cookies,
            'country': country
        })

    except requests.Timeout:
        result['error'] = '⏰ Timeout error. Unable to fetch the page within the specified time.'
    except Exception as e:
        result['error'] = f'❌ Error: {str(e)}'
    
    return result

def check_for_payment_gateways(headers, response_text, cookies):
    gateway_keywords = [
        'stripe', 'paypal', 'square', 'venmo', 'bitcoin', 'braintree', 'amazon-pay',
        'adyen', '2checkout', 'skrill', 'authorize.net', 'worldpay', 'payu', 'paytm',
        'afterpay', 'alipay', 'klarna', 'affirm', 'bluesnap', 'checkout.com', 'dwolla',
        'paddle', 'payoneer', 'sagepay', 'wechat pay', 'yandex.money', 'zelle',
        'shopify', 'buy now', 'add to cart', 'store', 'checkout', 'cart', 'shop now',
        'card', 'payment', 'gateway', 'checkout button', 'pay with'
    ]

    combined_text = response_text.lower() + str(headers).lower() + str(cookies).lower()
    detected_gateways = [keyword.capitalize() for keyword in gateway_keywords if keyword in combined_text]

    return detected_gateways

def check_for_cloudflare(response_text):
    cloudflare_markers = ['checking your browser', 'cf-ray', 'cloudflare']
    return any(marker in response_text.lower() for marker in cloudflare_markers)

def check_for_captcha(response_text):
    captcha_markers = ['recaptcha', 'g-recaptcha']
    return any(marker in response_text.lower() for marker in captcha_markers)

def check_for_graphql(response_text):
    graphql_markers = ['graphql', 'application/graphql']
    return any(marker in response_text.lower() for marker in graphql_markers)

def check_for_platform(response_text):
    platform_markers = {
        'woocommerce': ['woocommerce', 'wc-cart', 'wc-ajax'],
        'magento': ['magento', 'mageplaza'],
        'shopify': ['shopify', 'myshopify'],
        'prestashop': ['prestashop', 'addons.prestashop'],
        'opencart': ['opencart', 'route=common/home'],
        'bigcommerce': ['bigcommerce', 'stencil'],
        'wordpress': ['wordpress', 'wp-content'],
        'drupal': ['drupal', 'sites/all'],
        'joomla': ['joomla', 'index.php?option=com_']
    }

    for platform, markers in platform_markers.items():
        if any(marker in response_text.lower() for marker in markers):
            return platform.capitalize()

    return None

# Function to format the analysis results
def format_analysis_results(results):
    analysis = (
        f"🔍 𝐁𝟑 & 𝐒𝐓𝐑𝐈𝐏𝐄 𝐆𝐀𝐓𝐄𝐒 𝐒𝐍𝐈𝐏𝐄𝐑:\n"
        f"『𝗢𝗪𝗡𝗘𝗥』➜ @ddfmoto0\n"
        f"𝗨𝗥𝗟 ➜ {results['url']}\n"
        f"𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗚𝗔𝗧𝗘𝗪𝗔𝗬𝗦 ➜ {', '.join(results['payment_gateways']) if results['payment_gateways'] else 'None'}\n"
        f"𝗖𝗔𝗣𝗧𝗖𝗛𝗔 ➜ {'Yes' if results['captcha'] else 'No'}\n"
        f"𝗖𝗟𝗢𝗨𝗗𝗙𝗟𝗔𝗥𝗘 ➜ {'Yes' if results['cloudflare'] else 'No'}\n"
        f"𝗚𝗥𝗔𝗣𝗛𝗤𝗟 𝗗𝗘𝗧𝗘𝗖𝗧𝗘𝗗 ➜ {'Yes' if results['graphql'] else 'No'}\n"
        f"𝗣𝗟𝗔𝗧𝗙𝗢𝗥𝗠 ➜  {results['platform'] or 'Unknown'}\n"
    )
    return analysis

# Command handlers
def handle_url_command(chat_id, text):
    if text.startswith('/url '):
        url = text.split(' ', 1)[1]
        analyze_and_send(url, chat_id)
    elif 'url_list' in context_data.get(chat_id, {}):
        process_url_batches(chat_id, context_data[chat_id]['url_list'])
    else:
        send_message(chat_id, '⏳No URLs have been uploaded. Please upload a .txt file with URLs first.')

def handle_start_command(chat_id):
    send_message(chat_id, '🤖 Bot Status: Active ✅\n\n💀 Send .txt File with URLs Then use /url. For Manual checking Use /url <link>\n\n⚡ Join @sandaveX for more bot updates \n\n✨ Created with pride by @ddfmoto0🇮🇳')

def handle_file(chat_id, file_content):
    encodings = ['utf-8', 'latin-1', 'windows-1252']
    for encoding in encodings:
        try:
            urls = file_content.decode(encoding).splitlines()
            break
        except UnicodeDecodeError:
            continue
    else:
        send_message(chat_id, "❌ Error: Unable to decode file content. Please make sure the file is encoded in UTF-8, Latin-1, or Windows-1252.")
        return
    
    with lock:
        context_data[chat_id] = {'url_list': [url.strip() for url in urls if url.strip()]}
    send_message(chat_id, "🌿URLs have been uploaded. Reply with /url to start the analysis.")

def handle_cmds_command(chat_id):
    commands = (
        "/url - To analyze URLs from the uploaded .txt file or analyze a single URL if provided as /url <link>.\n"
        "/cmds - Available commands and their descriptions."
    )
    send_message(chat_id, commands)

def analyze_and_send(url, chat_id):
    result = analyze_site(url)
    analysis = format_analysis_results(result)
    messages = split_message(analysis)
    for message in messages:
        send_message(chat_id, message)
        time.sleep(2)  # Delay to handle rate limits

def process_url_batches(chat_id, url_list):
    for url in url_list:
        result = analyze_site(url)
        if 'Stripe' in result['payment_gateways'] or 'Braintree' in result['payment_gateways']:
            analyze_and_send(url, chat_id)
            time.sleep(2)  # Delay between checks

# Initialize context and user data
context_data = {}

# Main loop to process updates
def main():
    offset = None
    while True:
        updates = get_updates(offset)
        if 'result' in updates:
            for update in updates['result']:
                offset = update['update_id'] + 1
                
                if 'message' in update:
                    chat_id = update['message']['chat']['id']
                    text = update['message'].get('text')
                    document = update['message'].get('document')

                    if text:
                        if text.startswith('/start'):
                            handle_start_command(chat_id)
                        elif text.startswith('/url'):
                            thread = threading.Thread(target=handle_url_command, args=(chat_id, text))
                            thread.start()
                        elif text.startswith('/cmds'):
                            handle_cmds_command(chat_id)
                    elif document:
                        file_id = document['file_id']
                        file_info = requests.get(URL + 'getFile', params={'file_id': file_id}).json()
                        file_path = file_info['result']['file_path']
                        file_url = f'https://api.telegram.org/file/bot{TOKEN}/{file_path}'
                        file_content = requests.get(file_url).content
                        handle_file(chat_id, file_content)

if __name__ == '__main__':
    main()
