import os
import time
import asyncio
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

# ================= CONFIGS - MUDE DEPOIS DE TESTAR =================
TELEGRAM_TOKEN = "8742776802:AAHSzD1qTwCqMEOdoW9_pT2l5GfmMBWUZQY"
TELEGRAM_CHAT_ID = "7427648935"
USERNAME = "857789345"
PASSWORD = "max123ZICO"
SITE_URL = "https://www.elephantbet.co.mz/aviator/"
# ===================================================================

bot = Bot(token=TELEGRAM_TOKEN)

async def send_telegram_text_async(msg):
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
    except TelegramError as e:
        print(f"[ERRO TELEGRAM TEXT] {e}")
    except Exception as e:
        print(f"[ERRO TELEGRAM GERAL] {e}")

def send_telegram_text(msg):
    """Wrapper sync para chamar async"""
    asyncio.run(send_telegram_text_async(msg))

async def send_telegram_photo_async(bio, caption):
    try:
        await bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=bio,
            caption=caption
        )
    except Exception as e:
        print(f"[ERRO TELEGRAM PHOTO] {e}")

def send_telegram_screenshot(driver, step_name):
    try:
        png_data = driver.get_screenshot_as_png()
        img = Image.open(BytesIO(png_data))
        bio = BytesIO()
        img.save(bio, format='PNG')
        bio.seek(0)
        caption = f"🖥️ {step_name} - {time.strftime('%Y-%m-%d %H:%M:%S')}"
        asyncio.run(send_telegram_photo_async(bio, caption))
        print(f"[SCREENSHOT ENVIADO] {step_name}")
    except Exception as e:
        print(f"[ERRO SCREENSHOT] {e}")
        send_telegram_text(f"Erro ao enviar screenshot: {step_name}")

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
        # Seletores comuns para Aviator (Spribe) - ajuste se necessário inspecionando o site
        selectors = [
            ".payout-history .coefficient",
            ".history-multiplier",
            ".bubble-multiplier",
            "[class*='multiplier']",
            ".crash-history-item",
            ".history .value",
            ".recent-crashes span",
            ".multiplier-history .multiplier"
        ]
        
        history_texts = []
        for selector in selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                text = el.text.strip()
                if text and ('x' in text.lower() or text.isdigit() or '.' in text):
                    history_texts.append(text)
            if len(history_texts) >= 20:
                break
        
        return history_texts[:20]
    except Exception as e:
        print(f"[ERRO EXTRAÇÃO HISTÓRICO] {e}")
        return []

def main():
    send_telegram_text("🤖 Bot iniciado no Render - Aviator ElephantBet Scraper (PTB v22.6)")

    while True:
        driver = None
        try:
            driver = init_driver()
            send_telegram_text("Navegador iniciado. Acessando página...")
            driver.get(SITE_URL)
            send_telegram_screenshot(driver, "1. Página inicial / Aviator carregada")
            time.sleep(5)

            wait = WebDriverWait(driver, 25)

            # Tenta preencher username/telefone
            try:
                username_field = wait.until(EC.presence_of_element_located((By.ID, "username-login-page")))
                username_field.clear()
                username_field.send_keys(USERNAME)
                send_telegram_screenshot(driver, "2. Telefone/Username preenchido")
                time.sleep(5)
            except TimeoutException:
                send_telegram_text("⚠️ Campo username não encontrado (pode já estar logado ou layout mudou)")
                send_telegram_screenshot(driver, "Campo username não achado")

            # Senha
            try:
                password_field = driver.find_element(By.CSS_SELECTOR, 'input[type="password"][name="password"], input[placeholder*="Senha"]')
                password_field.clear()
                password_field.send_keys(PASSWORD)
                send_telegram_screenshot(driver, "3. Senha preenchida")
                time.sleep(5)
            except NoSuchElementException:
                send_telegram_text("⚠️ Campo senha não encontrado.")

            # Botão login
            try:
                login_button = driver.find_element(By.ID, "login-page")
                login_button.click()
                send_telegram_screenshot(driver, "4. Clicou em 'Conecte-se'")
                time.sleep(10)  # espera pós-login
            except NoSuchElementException:
                send_telegram_text("⚠️ Botão login não encontrado (pode já estar logado)")

            # Captura histórico inicial
            history = extract_history(driver)
            if history:
                msg = f"📊 Histórico recente ({len(history)} itens):\n" + " | ".join(history)
                send_telegram_text(msg)
                send_telegram_screenshot(driver, "5. Jogo carregado + Histórico visível")
            else:
                send_telegram_text("⚠️ Nenhum histórico detectado ainda. Pode precisar de aba 'Histórico' ou selector errado.")
                send_telegram_screenshot(driver, "5. Jogo carregado (sem histórico claro)")

            # Loop de monitoramento (atualiza a cada 30s, por ~15 min)
            for _ in range(30):
                time.sleep(30)
                try:
                    new_history = extract_history(driver)
                    if new_history:
                        latest = new_history[0] if new_history else "?"
                        send_telegram_text(f"🆕 Último multiplier: {latest}")
                except:
                    pass

        except Exception as e:
            error_msg = f"❌ Erro grave: {str(e)[:400]}... Reconectando em 60s"
            send_telegram_text(error_msg)
            print(error_msg)
        finally:
            if driver is not None:
                try:
                    driver.quit()
                except:
                    pass
        
        time.sleep(60)  # Delay entre tentativas completas de login

if __name__ == "__main__":
    main()
