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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, ElementNotInteractableException
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
        print(f"[TELEGRAM TEXT ENVIADO] {msg[:50]}...")
    except Exception as e:
        print(f"[ERRO TELEGRAM] {e}")

async def send_telegram_screenshot(driver, step_name: str):
    try:
        png_data = driver.get_screenshot_as_png()
        bio = BytesIO()
        Image.open(BytesIO(png_data)).save(bio, format='PNG')
        bio.seek(0)
        caption = f"🖥️ {step_name} - {time.strftime('%Y-%m-%d %H:%M:%S')}"
        await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=bio, caption=caption)
        print(f"[SCREENSHOT ENVIADO] {step_name}")
    except Exception as e:
        print(f"[ERRO SCREENSHOT] {e}")
        await send_telegram_text(f"Erro ao enviar screenshot: {step_name}")

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
        history = [el.get_attribute("innerText").strip() for el in elements if el.get_attribute("innerText").strip().endswith('x')]
        return history[:30]
    except Exception as e:
        print(f"[ERRO HISTÓRICO] {e}")
        return []

async def safe_send_keys(driver, element, text):
    try:
        element.send_keys(text)
    except ElementNotInteractableException:
        driver.execute_script("arguments[0].value = arguments[1];", element, text)

async def safe_click(driver, element):
    try:
        element.click()
    except ElementNotInteractableException:
        driver.execute_script("arguments[0].click();", element)

async def close_onesignal_popup(driver, wait):
    try:
        # Espera até 8s pro popup aparecer e botão ficar clicável
        cancel_btn = wait.until(EC.element_to_be_clickable((By.ID, "onesignal-slidedown-cancel-button")))
        await safe_click(driver, cancel_btn)
        await send_telegram_text("✅ Popup OneSignal 'NÃO' clicado com sucesso")
        await send_telegram_screenshot(driver, "Popup OneSignal fechado")
        await asyncio.sleep(3)  # tempo pra overlay sumir
    except TimeoutException:
        await send_telegram_text("Popup OneSignal não apareceu (ou já fechado) - continuando")
    except Exception as e:
        await send_telegram_text(f"Erro ao fechar OneSignal popup: {str(e)[:200]}")
        await send_telegram_screenshot(driver, "Erro fechando popup OneSignal")

async def main():
    await send_telegram_text("🤖 Bot iniciado - Fechando popup OneSignal antes do login")

    while True:
        driver = None
        try:
            driver = init_driver()
            await send_telegram_text("Acessando URL...")
            driver.get(SITE_URL)
            await send_telegram_screenshot(driver, "1. Página inicial carregada")

            wait = WebDriverWait(driver, 30)

            # Fecha o popup OneSignal slidedown ANTES de tentar login
            await close_onesignal_popup(driver, wait)

            # Tenta switch para iframe se login estiver dentro (fallback)
            try:
                iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
                driver.switch_to.frame(iframe)
                await send_telegram_text("Switch para iframe (login?)")
            except TimeoutException:
                pass  # sem iframe

            # Username
            try:
                username_el = wait.until(EC.element_to_be_clickable((By.ID, "username-login-page")))
                username_el.clear()
                await safe_send_keys(driver, username_el, USERNAME)
                await send_telegram_screenshot(driver, "2. Username preenchido")
                await asyncio.sleep(6)
            except Exception as e:
                await send_telegram_text(f"Erro username: {str(e)[:200]}")
                await send_telegram_screenshot(driver, "Erro username")

            # Senha
            try:
                password_el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="password"][name="password"], input[placeholder*="Senha"]')))
                password_el.clear()
                await safe_send_keys(driver, password_el, PASSWORD)
                await send_telegram_screenshot(driver, "3. Senha preenchida")
                await asyncio.sleep(6)
            except Exception as e:
                await send_telegram_text(f"Erro senha: {str(e)[:200]}")
                await send_telegram_screenshot(driver, "Erro senha")

            # Botão login
            try:
                login_btn = wait.until(EC.element_to_be_clickable((By.ID, "login-page")))
                await safe_click(driver, login_btn)
                await send_telegram_screenshot(driver, "4. Clicou em 'Conecte-se'")
                await asyncio.sleep(15)
            except Exception as e:
                await send_telegram_text(f"Erro clique login: {str(e)[:200]}")
                await send_telegram_screenshot(driver, "Erro clique login")

            driver.switch_to.default_content()  # sai de iframe se entrou

            # Histórico
            history = extract_history(driver)
            if history:
                msg = f"📊 Histórico ({len(history)}):\n{' | '.join(history)}"
                await send_telegram_text(msg)
                await send_telegram_screenshot(driver, "5. Histórico OK")
            else:
                await send_telegram_text("Sem histórico visível ainda")
                await send_telegram_screenshot(driver, "5. Sem histórico")

            # Monitora
            for _ in range(40):
                await asyncio.sleep(30)
                new_hist = extract_history(driver)
                if new_hist:
                    await send_telegram_text(f"🆕 Último: {new_hist[0] if new_hist else '?'}")

        except Exception as e:
            error_str = str(e)[:400]
            await send_telegram_text(f"❌ Erro: {error_str}... Reconectando")
            print(error_str)
            if driver:
                await send_telegram_screenshot(driver, f"ERRO: {error_str[:50]}")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
