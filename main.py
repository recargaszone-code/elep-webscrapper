# ... (imports e configs iguais ao anterior, copia do teu código)

async def js_fill(driver, selector, value):
    try:
        driver.execute_script(f"""
            var el = document.querySelector('{selector}');
            if (el) {{
                el.focus();
                el.value = '{value}';
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
                el.dispatchEvent(new Event('blur', {{bubbles: true}}));
            }}
        """)
        await send_telegram_text(f"JS fill + focus sucesso para {selector}")
        return True
    except Exception as e:
        await send_telegram_text(f"Erro JS fill: {str(e)[:150]}")
        return False

async def main():
    await send_telegram_text("🤖 Bot vRobust - Senha sempre via JS + mais delay")

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
                await send_telegram_text("✅ OneSignal fechado via JS")
                await send_telegram_screenshot(driver, "Popup fechado")
                await asyncio.sleep(8)
            except:
                await send_telegram_text("Sem popup OneSignal")

            # Username (tenta normal, fallback JS)
            try:
                username_el = wait.until(EC.element_to_be_clickable((By.ID, "username-login-page")))
                username_el.clear()
                username_el.send_keys(USERNAME)
                await send_telegram_screenshot(driver, "2. Username normal OK")
            except:
                await send_telegram_text("Username normal falhou - JS")
                await js_fill(driver, '#username-login-page', USERNAME)
                await send_telegram_screenshot(driver, "2. Username JS OK")

            await asyncio.sleep(8)

            # Senha - SEMPRE via JS agora (já que normal falha)
            await send_telegram_text("Preenchendo senha via JS (modo seguro)")
            success_senha = await js_fill(driver, 'input[name="password"]', PASSWORD)
            if success_senha:
                await send_telegram_screenshot(driver, "3. Senha preenchida via JS")
            else:
                await send_telegram_screenshot(driver, "3. Erro ao preencher senha via JS - veja print")

            await asyncio.sleep(10)  # tempo pro botão ativar

            # Botão login - sempre JS click
            try:
                login_btn = wait.until(EC.presence_of_element_located((By.ID, "login-page")))
                driver.execute_script("arguments[0].click();", login_btn)
                await send_telegram_text("Botão login clicado via JS")
                await send_telegram_screenshot(driver, "4. Login clicado")
                await asyncio.sleep(25)  # espera redirect + carregamento do jogo
            except Exception as e:
                await send_telegram_text(f"Erro botão login: {str(e)[:200]}")
                await send_telegram_screenshot(driver, "Erro botão login")

            # Histórico
            history = extract_history(driver)
            if history:
                msg = f"📊 Histórico recente ({len(history)}):\n" + " | ".join(history)
                await send_telegram_text(msg)
                await send_telegram_screenshot(driver, "5. Histórico capturado")
            else:
                await send_telegram_text("Nenhum histórico encontrado ainda (pode demorar pós-login)")
                await send_telegram_screenshot(driver, "5. Sem histórico visível")

            # Monitora
            for i in range(40):
                await asyncio.sleep(30)
                new_history = extract_history(driver)
                if new_history and (not history or new_history[0] != history[0]):
                    await send_telegram_text(f"🆕 Novo multiplier: {new_history[0]}")
                    history = new_history

        except Exception as e:
            await send_telegram_text(f"❌ Erro geral: {str(e)[:300]}")
            if driver:
                await send_telegram_screenshot(driver, "Erro geral - veja print")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
