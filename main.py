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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from telegram import Bot
from telegram.error import TelegramError

# ================= CONFIGS - MUDE DEPOIS =================
TELEGRAM_TOKEN = "8742776802:AAHSzD1qTwCqMEOdoW9_pT2l5GfmMBWUZQY"
TELEGRAM_CHAT_ID = "7427648935"
USERNAME = "857789345"
PASSWORD = "max123ZICO"
SITE_URL = "https://www.elephantbet.co.mz/aviator/"
# =========================================================

bot = Bot(token=TELEGRAM_TOKEN)

async def send_telegram_text(msg: str):
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
        print(f"[TELEGRAM TEXT ENVIADO] {msg[:50]}...")
    except TelegramError as e:
        print(f"[ERRO TELEGRAM TEXT] {e}")
    except Exception as e:
        print(f"[ERRO TELEGRAM GERAL] {e}")

async def send_telegram_screenshot(driver, step_name: str):
    try:
        png_data = driver.get_screenshot_as_png()
        img = Image.open(BytesIO(png_data))
        bio = BytesIO()
        img.save(bio, format='PNG')
        bio.seek(0)
        caption = f"🖥️ {step_name} - {time.strftime('%Y-%m-%d %H:%M:%S')}"
        await bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=bio,
            caption=caption
        )
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
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(executable_path=os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver"))
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except WebDriverException as e:
        print(f"[ERRO AO INICIAR DRIVER] {e}")
        raise

def extract_history(driver):
    try:
        # Seletor preciso: .payouts-block .payout (pega todos os multipliers)
        payout_elements = driver.find_elements(By.CSS_SELECTOR, ".payouts-block .payout")
        
        history_texts = []
        for el in payout_elements:
            text = el.get_attribute("innerText").strip()  # mais confiável que .text em alguns casos
            if text and text.endswith('x'):
                history_texts.append(text)
        
        # Inverte se quiser os mais recentes primeiro (testa no site)
        # history_texts = history_texts[::-1]  # descomenta se os últimos aparecerem no final
        return history_texts[:30]
    except Exception as e:
        print(f"[ERRO EXTRAÇÃO HISTÓRICO] {e}")
        return []

async def main():
    await send_telegram_text("🤖 Bot iniciado no Render - Aviator ElephantBet (Histórico Atualizado)")

    while True:
        driver = None
        try:
            driver = init_driver()
            await send_telegram_text("Navegador iniciado. Acessando página...")
            driver.get(SITE_URL)
            await send_telegram_screenshot(driver, "1. Página inicial / Aviator carregada")
            await asyncio.sleep(5)

            wait = WebDriverWait(driver, 25)

            # Username / Telefone
            try:
                username_field = await asyncio.to_thread(wait.until, EC.presence_of_element_located((By.ID, "username-login-page")))
                username_field.clear()
                username_field.send_keys(USERNAME)
                await send_telegram_screenshot(driver, "2. Telefone/Username preenchido")
                await asyncio.sleep(5)
            except TimeoutException:
                await send_telegram_text("⚠️ Campo username não encontrado (já logado?)")
                await send_telegram_screenshot(driver, "Campo username não achado")

            # Senha
            try:
                password_field = driver.find_element(By.CSS_SELECTOR, 'input[type="password"][name="password"], input[placeholder*="Senha"]')
                password_field.clear()
                password_field.send_keys(PASSWORD)
                await send_telegram_screenshot(driver, "3. Senha preenchida")
                await asyncio.sleep(5)
            except NoSuchElementException:
                await send_telegram_text("⚠️ Campo senha não encontrado.")

            # Login button
            try:
                login_button = driver.find_element(By.ID, "login-page")
                login_button.click()
                await send_telegram_screenshot(driver, "4. Clicou em 'Conecte-se'")
                await asyncio.sleep(10)
            except NoSuchElementException:
                await send_telegram_text("⚠️ Botão login não encontrado (já logado?)")

            # Histórico
            history = extract_history(driver)
            if history:
                msg = f"📊 Histórico recente ({len(history)} itens):\n" + " | ".join(history)
                await send_telegram_text(msg)
                await send_telegram_screenshot(driver, "5. Jogo carregado + Histórico visível")
            else:
                await send_telegram_text("⚠️ Nenhum histórico detectado. Verifique se logou e se o seletor mudou.")
                await send_telegram_screenshot(driver, "5. Jogo carregado (sem histórico claro)")

            # Monitora novos rounds
            last_known = set(history) if history else set()
            for _ in range(60):  # ~30 min de monitoramento antes de relogar
                await asyncio.sleep(30)
                try:
                    current = extract_history(driver)
                    if current:
                        new_ones = [m for m in current if m not in last_known]
                        if new_ones:
                            for m in new_ones:
                                await send_telegram_text(f"🆕 Novo multiplier: {m}")
                            last_known.update(new_ones)
                except:
                    pass

        except Exception as e:
            error_msg = f"❌ Erro grave: {str(e)[:400]}... Reconectando em 60s"
            await send_telegram_text(error_msg)
            print(error_msg)
        finally:
            if driver is not None:
                try:
                    driver.quit()
                except:
                    pass
        
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
