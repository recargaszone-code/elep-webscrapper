import time
import os
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from telegram import Bot

# Configs - NUNCA commit isso no git público!
TELEGRAM_TOKEN = "8742776802:AAHSzD1qTwCqMEOdoW9_pT2l5GfmMBWUZQY"
TELEGRAM_CHAT_ID = "7427648935"
USERNAME = "857789345"
PASSWORD = "max123ZICO"

SITE_URL = "https://www.elephantbet.co.mz/aviator/"

bot = Bot(token=TELEGRAM_TOKEN)

def send_telegram_text(msg):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
    except Exception as e:
        print(f"Erro Telegram text: {e}")

def send_telegram_screenshot(driver, step_name):
    try:
        png = driver.get_screenshot_as_png()
        img = Image.open(BytesIO(png))
        bio = BytesIO()
        img.save(bio, format='PNG')
        bio.seek(0)
        bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=bio,
            caption=f"🖥️ {step_name} - {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print(f"Screenshot enviado: {step_name}")
    except Exception as e:
        print(f"Erro screenshot: {e}")
        send_telegram_text(f"Erro ao enviar screenshot: {step_name}")

def init_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Tenta usar undetected_chromedriver pra menos detecção
    try:
        import undetected_chromedriver as uc
        driver = uc.Chrome(options=options, version_main=128)  # ajusta versão se precisar
    except:
        # fallback normal
        driver = webdriver.Chrome(options=options)
    
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def main():
    send_telegram_text("🤖 Bot iniciado no Render - Tentando login ElephantBet Aviator")
    
    while True:
        driver = None
        try:
            driver = init_driver()
            driver.get(SITE_URL)
            send_telegram_screenshot(driver, "1. Página inicial carregada")
            time.sleep(5)

            # Espera campo de username/telefone
            wait = WebDriverWait(driver, 20)
            username_field = wait.until(EC.presence_of_element_located((By.ID, "username-login-page")))
            username_field.clear()
            username_field.send_keys(USERNAME)
            send_telegram_screenshot(driver, "2. Username preenchido")
            time.sleep(5)

            # Senha
            password_field = driver.find_element(By.CSS_SELECTOR, 'input[type="password"][name="password"]')
            password_field.clear()
            password_field.send_keys(PASSWORD)
            send_telegram_screenshot(driver, "3. Senha preenchida")
            time.sleep(5)

            # Botão login
            login_btn = driver.find_element(By.ID, "login-page")
            login_btn.click()
            send_telegram_screenshot(driver, "4. Clicou em Login")
            time.sleep(8)  # espera redirect/carregar

            # Aqui assume que logou e jogo carregou
            # Procura histórico - Aviator da Spribe geralmente tem div com classe tipo .payouts-history ou .history
            try:
                history_elements = wait.until(EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ".payouts-history .bubble-multiplier, .history-item, [class*='multiplier']")
                ))
                history = [el.text.strip() for el in history_elements[:15]]  # últimos ~15
                send_telegram_text(f"📊 Histórico recente detectado:\n{' | '.join(history)}")
                send_telegram_screenshot(driver, "5. Jogo carregado + Histórico")
            except TimeoutException:
                send_telegram_text("⚠️ Não encontrou histórico visível. Pode estar em iframe ou precisar clicar em aba 'Histórico'.")
                send_telegram_screenshot(driver, "5. Jogo carregado (sem histórico claro)")

            # Fica monitorando a cada ~30s (ajusta)
            for _ in range(20):  # ~10 min antes de relogar
                time.sleep(30)
                try:
                    # Tenta atualizar histórico de novo
                    history_elements = driver.find_elements(By.CSS_SELECTOR, ".payouts-history .bubble-multiplier")
                    if history_elements:
                        latest = history_elements[0].text.strip()
                        send_telegram_text(f"🆕 Último multiplier: {latest}")
                except:
                    pass

        except Exception as e:
            send_telegram_text(f"❌ Erro grave: {str(e)[:200]}... Tentando novamente em 60s")
            print(e)
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
        time.sleep(60)  # delay entre tentativas completas

if __name__ == "__main__":
    main()