import os
import asyncio
import time
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, WebDriverException
from telegram import Bot
from telegram.error import TelegramError

# ================= CONFIGS =================
TELEGRAM_TOKEN = "8742776802:AAHSzD1qTwCqMEOdoW9_pT2l5GfmMBWUZQY"
TELEGRAM_CHAT_ID = "7427648935"
USERNAME = "857789345"
PASSWORD = "max123ZICO"
SITE_URL = "https://www.elephantbet.co.mz/aviator/"
# ===========================================

bot = Bot(token=TELEGRAM_TOKEN)

async def send_telegram_text(msg: str):
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
        print(f"[TELEGRAM] {msg[:50]}...")
    except Exception as e:
        print(f"[ERRO TELEGRAM] {e}")

async def send_telegram_screenshot(driver, step_name: str):
    try:
        png = driver.get_screenshot_as_png()
        bio = BytesIO()
        Image.open(BytesIO(png)).save(bio, format='PNG')
        bio.seek(0)
        await bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=bio,
            caption=f"🖥️ {step_name} - {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print(f"[SCREENSHOT] {step_name}")
    except Exception as e:
        print(f"[ERRO SCREENSHOT] {e}")
        await send_telegram_text(f"Erro print: {step_name}")

def init_driver():
    options = Options()
    options.binary_location = os.environ.get("CHROME_BIN", "/usr/bin/chromium")
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    service = Service(executable_path=os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver"))
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def extract_history(driver):
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, ".payouts-block .payout")
        history = [el.get_attribute("innerText").strip() for el in elements if el.get_attribute("innerText").strip() and 'x' in el.get_attribute("innerText")]
        return history[:30]
    except:
        return []

async def js_fill(driver, selector, value):
    try:
        driver.execute_script(f"""
            var el = document.querySelector('{selector}');
            if (el) {{
                el.value = '{value}';
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
                el.focus();
            }}
        """)
        await send_telegram_text(f"JS fill sucesso para {selector}")
    except Exception as e:
        await send_telegram_text(f"Erro JS fill: {str(e)[:150]}")

async def js_click(driver, selector):
    try:
        driver.execute_script(f"document.querySelector('{selector}').click();")
        await send_telegram_text(f"JS click sucesso para {selector}")
    except Exception as e:
        await send_telegram_text(f"Erro JS click: {str(e)[:150]}")

async def main():
    await send_telegram_text("🤖 Bot FINAL - Senha corrigida (name='password' + placeholder='Password')")

    while True:
        driver = None
        try:
            driver = init_driver()
            driver.get(SITE_URL)
            await send_telegram_screenshot(driver, "1. Página carregada")

            wait = WebDriverWait(driver, 40)

            # Fecha OneSignal popup
            try:
                cancel_btn = wait.until(EC.element_to_be_clickable((By.ID, "onesignal-slidedown-cancel-button")))
                driver.execute_script("arguments[0].click();", cancel_btn)
                await send_telegram_text("✅ OneSignal 'NÃO' clicado")
                await send_telegram_screenshot(driver, "Popup fechado")
                await asyncio.sleep(8)  # mais tempo pra estabilizar
            except TimeoutException:
                await send_telegram_text("Sem popup - ok")
            except Exception as e:
                await send_telegram_text(f"Erro popup: {str(e)[:150]}")

            # Username
            try:
                username_el = wait.until(EC.element_to_be_clickable((By.ID, "username-login-page")))
                username_el.clear()
                username_el.send_keys(USERNAME)
                await send_telegram_screenshot(driver, "2. Username preenchido")
            except Exception as e:
                await send_telegram_text(f"Username normal falhou: {str(e)[:150]} - JS")
                await js_fill(driver, '#username-login-page', USERNAME)
                await send_telegram_screenshot(driver, "2. Username via JS")

            await asyncio.sleep(8)  # tempo pro JS ativar senha

            # Senha - seletor corrigido por name="password" (mais seguro)
            try:
                password_el = wait.until(EC.element_to_be_clickable((By.NAME, "password")))
                password_el.clear()
                password_el.send_keys(PASSWORD)
                await send_telegram_screenshot(driver, "3. Senha preenchida (name='password')")
            except Exception as e:
                await send_telegram_text(f"Senha normal falhou: {str(e)[:150]} - usando JS")
                await js_fill(driver, 'input[name="password"]', PASSWORD)
                await send_telegram_screenshot(driver, "3. Senha via JS")

            await asyncio.sleep(6)

            # Botão login - ID "login-page"
            try:
                login_btn = wait.until(EC.element_to_be_clickable((By.ID, "login-page")))
                driver.execute_script("arguments[0].click();", login_btn)  # JS pra evitar not interactable
                await send_telegram_screenshot(driver, "4. Login clicado")
                await asyncio.sleep(20)
            except Exception as e:
                await send_telegram_text(f"Erro botão: {str(e)[:150]}")
                await send_telegram_screenshot(driver, "Erro botão")

            # Histórico
            history = extract_history(driver)
            if history:
                await send_telegram_text(f"📊 Histórico ({len(history)}): {' | '.join(history)}")
                await send_telegram_screenshot(driver, "5. Histórico OK")
            else:
                await send_telegram_text("Sem histórico - espera pós-login")
                await send_telegram_screenshot(driver, "5. Sem histórico")

            # Monitor simples
            for _ in range(30):
                await asyncio.sleep(30)
                new_hist = extract_history(driver)
                if new_hist:
                    await send_telegram_text(f"🆕 Último: {new_hist[0] if new_hist else '?'}")

        except Exception as e:
            await send_telegram_text(f"❌ Erro: {str(e)[:300]}")
            if driver:
                await send_telegram_screenshot(driver, "Erro geral")
        finally:
            if driver:
                driver.quit()

        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
