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
from telegram import Bot

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
        await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=bio, caption=f"🖥️ {step_name} - {time.strftime('%Y-%m-%d %H:%M:%S')}")
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
                el.click();
                el.focus();
                el.value = '{value}';
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
            }}
        """)
        await send_telegram_text(f"✅ Preenchido com JS: {selector}")
        return True
    except Exception as e:
        await send_telegram_text(f"Erro JS: {str(e)[:150]}")
        return False

async def main():
    await send_telegram_text("🤖 Bot vFINAL - Usando os IDs e classes exatos que tu mandou (sem confusão de forms)")

    while True:
        driver = None
        try:
            driver = init_driver()
            driver.get(SITE_URL)
            await send_telegram_screenshot(driver, "1. Página carregada")

            wait = WebDriverWait(driver, 40)

            # Fecha OneSignal
            try:
                cancel_btn = wait.until(EC.presence_of_element_located((By.ID, "onesignal-slidedown-cancel-button")))
                driver.execute_script("arguments[0].click();", cancel_btn)
                await send_telegram_text("✅ OneSignal fechado")
                await send_telegram_screenshot(driver, "Popup fechado")
                await asyncio.sleep(8)
            except:
                await send_telegram_text("Sem popup")

            # Username - ID exato que tu mandou
            await send_telegram_text("Preenchendo username (ID: username-login-form-oneline)")
            await js_fill(driver, '#username-login-form-oneline', USERNAME)
            await send_telegram_screenshot(driver, "2. Username preenchido")

            await asyncio.sleep(8)

            # Senha - classe exata que tu mandou
            await send_telegram_text("Preenchendo senha (classe: bto-form-control-password)")
            await js_fill(driver, '.bto-form-control-password', PASSWORD)
            await send_telegram_screenshot(driver, "3. Senha preenchida")

            await asyncio.sleep(10)

            # Botão login
            try:
                login_btn = wait.until(EC.presence_of_element_located((By.ID, "login-page")))
                driver.execute_script("arguments[0].click();", login_btn)
                await send_telegram_text("✅ Login clicado")
                await send_telegram_screenshot(driver, "4. Login clicado")
                await asyncio.sleep(25)
            except Exception as e:
                await send_telegram_text(f"Erro botão: {str(e)[:200]}")
                await send_telegram_screenshot(driver, "Erro botão")

            # Histórico
            history = extract_history(driver)
            if history:
                msg = f"📊 Histórico ({len(history)}):\n" + " | ".join(history)
                await send_telegram_text(msg)
                await send_telegram_screenshot(driver, "5. Histórico OK")
            else:
                await send_telegram_text("Sem histórico ainda")
                await send_telegram_screenshot(driver, "5. Sem histórico")

            for _ in range(40):
                await asyncio.sleep(30)
                new_hist = extract_history(driver)
                if new_hist:
                    await send_telegram_text(f"🆕 Último: {new_hist[0]}")

        except Exception as e:
            await send_telegram_text(f"❌ Erro: {str(e)[:300]}")
            if driver:
                await send_telegram_screenshot(driver, "Erro geral")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
