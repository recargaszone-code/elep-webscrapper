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
        # Espera o payouts-block usando teu XPATH full
        payouts_block = driver.find_element(By.XPATH, "/html/body/app-root/app-game/div/div[1]/div[2]/div/div[2]/div[2]/app-stats-widget/div/div[1]")
        # Pega todos os .payout dentro dele
        elements = payouts_block.find_elements(By.CSS_SELECTOR, "div.payout")
        history = [el.get_attribute("innerText").strip() for el in elements if el.get_attribute("innerText").strip() and 'x' in el.get_attribute("innerText")]
        if not history:
            # Fallback para teu JS Path convertido para XPATH
            elements = driver.find_elements(By.XPATH, "//body/app-root/app-game/div/div[@class='main-container']/div[@class='w-100 h-100']/div/div[@class='game-play']/div[@class='result-history disabled-on-game-focused']/app-stats-widget/div/app-stats-dropdown/div/div[@class='payouts-block']/div[@class='payout ng-star-inserted']")
            history = [el.get_attribute("innerText").strip() for el in elements if el.get_attribute("innerText").strip() and 'x' in el.get_attribute("innerText")]
        return history[:30]
    except Exception as e:
        print(f"[ERRO extract] {e}")
        return []

async def js_fill(driver, selector, value):
    try:
        driver.execute_script(f"""
            var el = document.querySelector('{selector}');
            if (el) {{ el.click(); el.focus(); el.value = '{value}';
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
            }}
        """)
        return True
    except:
        return False

async def main():
    await send_telegram_text("🤖 Bot vFINAL - Histórico com teu XPATH full + fallback JS Path")

    while True:
        driver = None
        try:
            driver = init_driver()
            driver.get(SITE_URL)
            await send_telegram_screenshot(driver, "1. Página carregada")

            wait = WebDriverWait(driver, 50)

            # Login
            try:
                cancel_btn = wait.until(EC.presence_of_element_located((By.ID, "onesignal-slidedown-cancel-button")))
                driver.execute_script("arguments[0].click();", cancel_btn)
            except: pass

            await js_fill(driver, '#username-login-form-oneline', USERNAME)
            await asyncio.sleep(8)
            await js_fill(driver, '.bto-form-control-password', PASSWORD)
            await asyncio.sleep(10)

            login_btn = wait.until(EC.presence_of_element_located((By.ID, "login-form-oneline")))
            driver.execute_script("arguments[0].click();", login_btn)
            await send_telegram_screenshot(driver, "4. Login clicado")
            await asyncio.sleep(15)

            # Iframe
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "game_loader")))
            await send_telegram_text("✅ Entrou no iframe")
            await send_telegram_screenshot(driver, "5. Iframe carregado")

            await asyncio.sleep(25)

            # Wait forte até payouts-wrapper aparecer (teu XPATH)
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/app-root/app-game/div/div[1]/div[2]/div/div[2]/div[2]/app-stats-widget/div/div[1]")))
                await send_telegram_text("✅ Payouts-wrapper detectado!")
            except:
                await send_telegram_text("⚠️ Payouts-wrapper não encontrado")

            await send_telegram_screenshot(driver, "6. Tela do jogo com histórico visível")

            # Extrai
            history = extract_history(driver)
            await send_telegram_text(f"🔍 Encontrados {len(history)} multipliers")

            if history:
                msg = f"📊 HISTÓRICO AVIATOR (30 valores):\n{str(history)}"
                await send_telegram_text(msg)
                await send_telegram_screenshot(driver, "7. Histórico enviado!")
            else:
                await send_telegram_text("❌ Sem multipliers - tenta mais delay no próximo ciclo")
                await send_telegram_screenshot(driver, "7. Sem histórico")

            # Monitora
            for _ in range(50):
                await asyncio.sleep(30)
                new_hist = extract_history(driver)
                if new_hist and (not history or new_hist[0] != history[0]):
                    await send_telegram_text(f"🆕 Novo: {new_hist[0]}")
                    history = new_hist

        except Exception as e:
            await send_telegram_text(f"❌ Erro: {str(e)[:300]}")
            if driver:
                await send_telegram_screenshot(driver, "Erro geral")
        finally:
            if driver:
                try:
                    driver.switch_to.default_content()
                    driver.quit()
                except: pass

        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
