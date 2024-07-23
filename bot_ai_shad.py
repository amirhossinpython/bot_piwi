import asyncio
import random
import os
import subprocess
import sys
from io import BytesIO
import shutil
import re

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import aiosqlite
except ImportError:
    install('aiosqlite')
    import aiosqlite

try:
    import requests
except ImportError:
    install('requests')
    import requests

try:
    
    from shadpy import Client, filters, utils
    from shadpy.types import Updates
except ImportError:
    install('shadpy')
    
    from shadpy import Client, filters, utils
    from shadpy.types import Updates

try:
    import qrcode
except ImportError:
    install("qrcode")
    import qrcode

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError :
    install("pillow")

ADMIN_GUID = 'guid'  # شناسه چت ادمین
def read_bad_words(file_path):
    with open(file_path, "r", encoding="utf-8") as file:  # تغییر کدگذاری به utf-8
        words = [line.strip() for line in file if line.strip()]
    return words

# ایجاد الگوهای منظم برای شناسایی انواع کلمات مستهجن و سانسور شده
def create_patterns(words):
    patterns = []
    for word in words:
        # ایجاد الگو برای شناسایی کلمات با انواع مختلف سانسور
        pattern = re.escape(word)
        pattern = pattern.replace(r'\ ', r'\s*')
        pattern = pattern.replace(r'\*', r'\s*')
        patterns.append(re.compile(r'\b{}\b'.format(pattern), re.IGNORECASE))
    return patterns

# خواندن کلمات از فایل متنی
bad_words = read_bad_words("bad_words.txt")
bad_patterns = create_patterns(bad_words)

def contains_prohibited_word(text, patterns):
    """
    بررسی می‌کند که آیا متن شامل کلمات مستهجن است یا خیر.
    """
    text = text.lower()  # تبدیل متن به حروف کوچک برای مقایسه
    for pattern in patterns:
        if pattern.search(text):
            return True
    return False

list_order="""
### لیست خدمات و نحوه استفاده:

1. **/start**  
   - **توضیحات**: برای شروع استفاده از ربات و ثبت نام اولیه. بعد از ارسال این دستور، ربات از شما اطلاعات پایه مانند نام، شماره تلفن و مکان زندگی را درخواست خواهد کرد.

2. **/change_service**  
   - **توضیحات**: برای تغییر سرویس انتخابی خود. پس از ارسال این دستور، ربات از شما درخواست می‌کند که سرویس جدید خود را انتخاب کنید:
     1. چت با هوش مصنوعی
     2. تبدیل لینک به کیو آر کد
     3. خدمات خط‌های باستانی
     4. تبدیل متن به لوگو
     5. تولید تصویر با هوش مصنوعی

3. **/delete**  
   - **توضیحات**: برای حذف حساب کاربری شما. پس از ارسال این دستور، حساب کاربری شما حذف می‌شود و می‌توانید دوباره با ارسال دستور /start ثبت نام کنید.

4. **چت با هوش مصنوعی**  
   - **توضیحات**: اگر این سرویس را انتخاب کنید، می‌توانید سوالات خود را ارسال کنید و ربات به آن‌ها پاسخ خواهد داد.

5. **تبدیل لینک به کیو آر کد**  
   - **توضیحات**: اگر این سرویس را انتخاب کنید، لینک خود را ارسال کنید و ربات یک کیو آر کد برای شما تولید خواهد کرد.

6. **خدمات خط‌های باستانی**  
   - **توضیحات**: اگر این سرویس را انتخاب کنید، متن خود را ارسال کنید تا به خط‌های باستانی مانند خط میخی، پهلوی و مانوی تبدیل شود.

7. **تبدیل متن به لوگو**  
   - **توضیحات**: اگر این سرویس را انتخاب کنید، متن خود را ارسال کنید و ربات یک لوگو برای شما تولید خواهد کرد.

8. **تولید تصویر با هوش مصنوعی**  
   - **توضیحات**: اگر این سرویس را انتخاب کنید، متن خود را ارسال کنید و ربات یک تصویر مرتبط با آن متن تولید خواهد کرد.

    
"""
bot = Client(name='shadpy')

if os.path.exists('users.db'):
    os.remove('users.db')

async def init_db():
    async with aiosqlite.connect('users.db') as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
                                user_id TEXT PRIMARY KEY,
                                username TEXT,
                                phone TEXT,
                                location TEXT,
                                age INTEGER,
                                account_number TEXT,
                                qr_code_url TEXT,
                                selected_service TEXT)''')
        await db.commit()

asyncio.run(init_db())

async def save_user(user_id, username, phone, location, age, account_number, qr_code_url=None, selected_service=None):
    async with aiosqlite.connect('users.db') as db:
        await db.execute('''INSERT INTO users 
                            (user_id, username, phone, location, age, account_number, qr_code_url, selected_service) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                         (user_id, username, phone, location, age, account_number, qr_code_url, selected_service))
        await db.commit()

async def update_user(user_id, username=None, phone=None, location=None, age=None, account_number=None, qr_code_url=None, selected_service=None):
    async with aiosqlite.connect('users.db') as db:
        if username:
            await db.execute('UPDATE users SET username = ? WHERE user_id = ?', (username, user_id))
        if phone:
            await db.execute('UPDATE users SET phone = ? WHERE user_id = ?', (phone, user_id))
        if location:
            await db.execute('UPDATE users SET location = ? WHERE user_id = ?', (location, user_id))
        if age:
            await db.execute('UPDATE users SET age = ? WHERE user_id = ?', (age, user_id))
        if account_number:
            await db.execute('UPDATE users SET account_number = ? WHERE user_id = ?', (account_number, user_id))
        if qr_code_url:
            await db.execute('UPDATE users SET qr_code_url = ? WHERE user_id = ?', (qr_code_url, user_id))
        if selected_service:
            await db.execute('UPDATE users SET selected_service = ? WHERE user_id = ?', (selected_service, user_id))
        await db.commit()

async def reset_user_service(user_id):
    async with aiosqlite.connect('users.db') as db:
        await db.execute('UPDATE users SET selected_service = NULL WHERE user_id = ?', (user_id,))
        await db.commit()

async def send_info_to_admin(user_id):
    async with aiosqlite.connect('users.db') as db:
        async with db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cursor:
            user = await cursor.fetchone()
    if user:
        username, phone, location, age, account_number, qr_code_url, selected_service = user[1], user[2], user[3], user[4], user[5], user[6], user[7]
        message = (f"کاربر جدید ثبت نام کرد:\n"
                   f"شناسه: {user_id}\n"
                   f"نام: {username}\n"
                   f"شماره تلفن: {phone}\n"
                   f"مکان: {location}\n"
                   f"سن: {age}\n"
                   f"شماره حساب: {account_number}\n"
                   f"لینک کیو آر کد: {qr_code_url}\n"
                   f"خدمت انتخاب شده: {selected_service}")
        await bot.send_message(ADMIN_GUID, message)

def chatgpt(text):
    s = requests.Session()
    api_urls = [
        f"http://api-free.ir/api/bard.php?text={text}",
        f"https://api.chbk.run/chatgpt?text={text}"
    ]
    
    try:
        selected_url = random.choice(api_urls)
        response = s.get(selected_url)
        response.raise_for_status()  
        
        if 'bard.php' in selected_url:
            chat = response.json().get("result")
        else:
            chat = response.json().get("data")
        
        return chat
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"
    except KeyError:
        return "Error: Unexpected response format."

def create_qr_code(url, filename):
    qr = qrcode.make(url)
    qr.save(filename)

def photo_ai(text,file_name):
    try:
        response = requests.get(f"http://api-free.ir/api/img.php?text={text}&v=3.5")
        response.raise_for_status()
        data = response.json()
        result = data["result"]
        random_link = random.choice(result)
        response = requests.get(random_link, stream=True)
        response.raise_for_status()
        with open(file_name, "wb") as out_file:
            shutil.copyfileobj(response.raw, out_file)
          # Open the image file
        return "Image downloaded and saved as 'downloaded_image.jpg'."
    except requests.RequestException as e:
        return f"Error: Unable to download image. {str(e)}"
english_to_cuneiform_mapping = {
    'a': '𒀀', 'b': '𒁀', 'c': '𒄀', 'd': '𒁲', 'e': '𒂊',
    'f': '𒆳', 'g': '𒄖', 'h': '𒄩', 'i': '𒄿', 'j': '𒋛',
    'k': '𒆠', 'l': '𒇻', 'm': '𒈠', 'n': '𒉈', 'o': '𒌋',
    'p': '𒉿', 'q': '𒆥', 'r': '𒊑', 's': '𒊍', 't': '𒋗',
    'u': '𒌑', 'v': '𒅅', 'w': '𒉿', 'x': '𒍝', 'y': '𒅀',
    'z': '𒍣',
    'A': '𒀀', 'B': '𒁀', 'C': '𒄀', 'D': '𒁲', 'E': '𒂊',
    'F': '𒆳', 'G': '𒄖', 'H': '𒄩', 'I': '𒄿', 'J': '𒋛',
    'K': '𒆠', 'L': '𒇻', 'M': '𒈠', 'N': '𒉈', 'O': '𒌋',
    'P': '𒉿', 'Q': '𒆥', 'R': '𒊑', 'S': '𒊍', 'T': '𒋗',
    'U': '𒌑', 'V': '𒅅', 'W': '𒉿', 'X': '𒍝', 'Y': '𒅀',
    'Z': '𒍣'
}

persian_to_cuneiform_mapping = {
    'آ': '𒀀', 'ا': '𒀀', 'ب': '𒁀', 'پ': '𒁀', 'ت': '𒁲',
    'ث': '𒁲', 'ج': '𒄀', 'چ': '𒄀', 'ح': '𒄩', 'خ': '𒄩',
    'د': '𒁲', 'ذ': '𒁲', 'ر': '𒊑', 'ز': '𒍣', 'ژ': '𒍣',
    'س': '𒊍', 'ش': '𒊍', 'ص': '𒋗', 'ض': '𒋗', 'ط': '𒋗',
    'ظ': '𒋗', 'ع': '𒆳', 'غ': '𒆳', 'ف': '𒆥', 'ق': '𒆥',
    'ک': '𒆠', 'گ': '𒄖', 'ل': '𒇻', 'م': '𒈠', 'ن': '𒉈',
    'و': '𒌋', 'ه': '𒂊', 'ی': '𒅀'
}

persian_to_pahlavi_mapping = {
    'آ': '𐎠', 'ا': '𐎠', 'ب': '𐎡', 'پ': '𐎡', 'ت': '𐎮',
    'ث': '𐎮', 'ج': '𐎤', 'چ': '𐎤', 'ح': '𐎢', 'خ': '𐎢',
    'د': '𐎣', 'ذ': '𐎣', 'ر': '𐎼', 'ز': '𐎳', 'ژ': '𐎳',
    'س': '𐎴', 'ش': '𐎴', 'ص': '𐎧', 'ض': '𐎧', 'ط': '𐎧',
    'ظ': '𐎧', 'ع': '𐎦', 'غ': '𐎦', 'ف': '𐎦', 'ق': '𐎦',
    'ک': '𐎠', 'گ': '𐎵', 'ل': '𐎲', 'م': '𐎫', 'ن': '𐎱',
    'و': '𐎺', 'ه': '𐎺', 'ی': '𐎡'
}

persian_to_manavi_mapping = {
    'آ': '𐡀', 'ا': '𐡀', 'ب': '𐡁', 'پ': '𐡁', 'ت': '𐡊',
    'ث': '𐡊', 'ج': '𐡄', 'چ': '𐡄', 'ح': '𐡂', 'خ': '𐡂',
    'د': '𐡃', 'ذ': '𐡃', 'ر': '𐡎', 'ز': '𐡍', 'ژ': '𐡍',
    'س': '𐡌', 'ش': '𐡌', 'ص': '𐡇', 'ض': '𐡇', 'ط': '𐡇',
    'ظ': '𐡇', 'ع': '𐡆', 'غ': '𐡆', 'ف': '𐡆', 'ق': '𐡆',
    'ک': '𐡀', 'گ': '𐡅', 'ل': '𐡋', 'م': '𐡉', 'ن': '𐡈',
    'و': '𐡏', 'ه': '𐡏', 'ی': '𐡁'
}

def fetch_random_logo(text):
    page = random.randint(1, 99)
    url = f"https://api-free.ir/api/Logo-top.php?text={text}&page={page}"

    try:
        response = requests.get(url)
        data = response.json()
        if 'result' in data and data['result']:
            # انتخاب یک لینک تصادفی از لیست لینک‌های لوگوها
            random_logo_url = random.choice(data['result'])
            return random_logo_url
        else:
            return None
    except Exception as e:
        print(f"Error fetching logo: {e}")
        return None

def download_logo_and_save(text):
    random_logo_url = fetch_random_logo(text)
    if random_logo_url:
        try:
            response = requests.get(random_logo_url)
            image = Image.open(BytesIO(response.content))
            # ذخیره تصویر در فایل سیستم
            file_name = f"{text}_logo.png"
            image.save(file_name)
            print(f"Logo saved successfully as {file_name}.")
        except Exception as e:
            print("Error occurred while saving logo:", e)
    else:
        print("No logos found.")

def text_to_cuneiform(text):
    cuneiform_text = ""
    for char in text:
        if char in english_to_cuneiform_mapping:
            cuneiform_text += english_to_cuneiform_mapping[char]
        elif char in persian_to_cuneiform_mapping:
            cuneiform_text += persian_to_cuneiform_mapping[char]
        else:
            cuneiform_text += char
    return cuneiform_text

def text_to_pahlavi(text):
    pahlavi_text = ""
    for char in text:
        if char in persian_to_pahlavi_mapping:
            pahlavi_text += persian_to_pahlavi_mapping[char]
        else:
            pahlavi_text += char
    return pahlavi_text

def text_to_manavi(text):
    manavi_text = ""
    for char in text:
        if char in persian_to_manavi_mapping:
            manavi_text += persian_to_manavi_mapping[char]
        else:
            manavi_text += char
    return manavi_text



@bot.on_message_updates(filters.Commands(["start"]), filters.is_private)
async def start_message(update: Updates):
    user_id = update.object_guid
    async with aiosqlite.connect('users.db') as db:
        async with db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cursor:
            user = await cursor.fetchone()

    if not user:
        await save_user(user_id, '', '', '', None, '', '')
        await update.reply("سلام! لطفا نام خود را ارسال کنید.")
    else:
        await update.reply("شما قبلاً ثبت نام کرده‌اید.")

@bot.on_message_updates(filters.Commands(["change_service"]), filters.is_private)
async def change_service(update: Updates):
    user_id = update.object_guid
    async with aiosqlite.connect('users.db') as db:
        async with db.execute('SELECT selected_service FROM users WHERE user_id = ?', (user_id,)) as cursor:
            user = await cursor.fetchone()

    if user:
        await reset_user_service(user_id)  # غیرفعال کردن سرویس قبلی
        await update.reply("لطفا خدماتی که می‌خواهید استفاده کنید را انتخاب کنید:\n1. چت با هوش مصنوعی\n2. تبدیل لینک به کیو آر کد\n3. خدمات خط‌های باستانی\n4. تبدیل متن به لوگو\n5. دریافت تصویر با استفاده از هوش مصنوعی")  # اضافه کردن گزینه 5
    else:
        await update.reply("لطفا ابتدا دستور /start را ارسال کنید و ثبت نام کنید.")



@bot.on_message_updates(filters.Commands(["delete"]), filters.is_private)
async def delete_account(update: Updates):
    user_id = update.object_guid
    async with aiosqlite.connect('users.db') as db:
        await db.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        await db.commit()
    await update.reply("حساب کاربری شما با موفقیت حذف شد. لطفا دوباره ثبت نام کنید با ارسال دستور /start.")


@bot.on_message_updates(filters.is_private)
async def handle_message(update: Updates):
    user_id = update.object_guid
    text = update.text.strip()

    async with aiosqlite.connect('users.db') as db:
        async with db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cursor:
            user = await cursor.fetchone()

    if user:
        if user[1] == '':
            await update_user(user_id, username=text)
            await update.reply("لطفا شماره تلفن خود را ارسال کنید.")
        elif user[2] == '':
            await update_user(user_id, phone=text)
            await update.reply("لطفا مکان زندگی خود را ارسال کنید.")
        elif user[3] == '':
            await update_user(user_id, location=text)
            await update.reply("لطفا سن خود را ارسال کنید.")
        elif user[4] is None:
            if text.isdigit():
                await update_user(user_id, age=int(text))
                await update.reply("لطفا شماره حساب خود را ارسال کنید.")
            else:
                await update.reply("لطفا سن خود را به صورت عددی وارد کنید.")
        elif user[5] == '':
            await update_user(user_id, account_number=text)
            await update.reply("ثبت نام شما کامل شد. خوش آمدید! لطفا خدماتی که می‌خواهید استفاده کنید را انتخاب کنید:\n1. چت با هوش مصنوعی\n2. تبدیل لینک به کیو آر کد\n3. خدمات خط‌های باستانی\n4. تبدیل متن به لوگو\n5. دریافت تصویر با استفاده از هوش مصنوعی")  # اضافه کردن گزینه 5
        elif user[7] is None:
            if text == '1':
                await update_user(user_id, selected_service='chat')
                await update.reply("شما خدمت چت با هوش مصنوعی را انتخاب کرده‌اید. سوال خود را ارسال کنید.")
            elif text == '2':
                await update_user(user_id, selected_service='qr')
                await update.reply("شما خدمت تبدیل لینک به کیو آر کد را انتخاب کرده‌اید. لینک خود را ارسال کنید.")
            elif text == '3':
                await update_user(user_id, selected_service='ancient_texts')
                await update.reply("شما خدمت تبدیل متن به خط‌های باستانی را انتخاب کرده‌اید. متن خود را ارسال کنید.")
            elif text == '4':
                await update_user(user_id, selected_service='logo')
                await update.reply("شما خدمت تبدیل متن به لوگو را انتخاب کرده‌اید. متن خود را ارسال کنید.")
            elif text == '5':
                await update_user(user_id, selected_service='photo_ai')
                await update.reply("شما خدمت دریافت تصویر با استفاده از هوش مصنوعی را انتخاب کرده‌اید. متن خود را ارسال کنید.")
            else:
                await update.reply("لطفا یک گزینه معتبر انتخاب کنید:\n1. چت با هوش مصنوعی\n2. تبدیل لینک به کیو آر کد\n3. خدمات خط‌های باستانی\n4. تبدیل متن به لوگو\n5. دریافت تصویر با استفاده از هوش مصنوعی")
        else:
            if user[7] == 'chat':
                await update.reply("منتظر پاسخ ربات باشید")
                ai_response = chatgpt(text)
                await update.reply(ai_response)
            elif user[7] == 'qr':
                qr_image = create_qr_code(text, "out.png")
                with open("out.png", "rb") as p:
                    await update.reply("منتظر ساخت کیو آر کد باشید")
                    await update.reply_photo("out.png", caption="این کد کیو آر برای لینک شماست.")
                await update_user(user_id, qr_code_url=text)  # ذخیره لینک کیو آر کد در دیتابیس
            elif user[7] == 'ancient_texts':
                cuneiform_text = text_to_cuneiform(text)
                pahlavi_text = text_to_pahlavi(text)
                manavi_text = text_to_manavi(text)
                await update.reply(f"متن شما به خط‌های باستانی:\n\nخط میخی:\n{cuneiform_text}\n\nپهلوی:\n{pahlavi_text}\n\nمانی:\n{manavi_text}")
            elif user[7] == 'logo':
                await update.reply("منتظر ایجاد لوگو باشید.")
                download_logo_and_save(text)
                file_name = f"{text}_logo.png"
                with open(file_name, "rb") as p:
                    await update.reply_photo(str(file_name), caption="این لوگوی متن شماست.")
            elif user[7] == 'photo_ai':
                await update.reply("منتظر دریافت تصویر باشید.")
                result_message = photo_ai(text,"downloaded_image_ai.jpg")
                try:
                    
                    with open('downloaded_image_ai.jpg',"rb") as p:
                        await update.reply("**الان میدم خدمت شما**")
                        await update.reply_photo("downloaded_image_ai.jpg",caption="تصویر شما اماده شد ")
                except Exception as im:
                    await update.reply(F"erorr:{im}")
            else:
                await update.reply("لطفا ابتدا خدمات مورد نظر خود را انتخاب کنید.")
    else:
        await update.reply("لطفا ابتدا دستور /start را ارسال کنید.")



@bot.on_message_updates(filters.is_private,filters.Commands(["دستورات"],prefixes=''))
async def send_command(update: Updates):
    await update.reaction(2)
    
    await update.reply(list_order)
    

@bot.on_message_updates(filters.is_private)
async def block_user(update: Updates):
 
    if contains_prohibited_word(update.text, bad_patterns):
        await update.reply("پیام شما حاوی محتوای غیر اخلاقی است و شما بلاک شدید.")
        await update.block()

bot.run()




