from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from io import BytesIO

app = Flask(__name__)
CORS(app)

REQUIRED_FIELDS = ['longueur_palette', 'largeur_palette', 'hauteur_colis',
                   'longueur_colis', 'largeur_colis', 'poids_colis']

@app.route('/generate-palette', methods=['POST'])
def generate_palette():
    data = request.json
    if not data:
        return jsonify({'error': 'JSON invalide ou manquant'}), 400

    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        return jsonify({'error': f'Champs manquants : {missing}'}), 400

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.binary_location = "/usr/bin/chromium"

    driver = None
    try:
        driver = webdriver.Chrome(
            service=Service("/usr/bin/chromedriver"),
            options=chrome_options
        )

        driver.get("https://www.onpallet.com/fr/calculateur-de-palettes")

        dropdown_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button#palletselect"))
        )
        dropdown_button.click()

        custom_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a#ps_palX"))
        )
        custom_option.click()

        longueur_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input#ps_custL"))
        )
        largeur_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input#ps_custW"))
        )

        longueur_input.clear()
        longueur_input.send_keys(str(data['longueur_palette']))
        largeur_input.clear()
        largeur_input.send_keys(str(data['largeur_palette']))

        for field_id, key in [
            ("p_height", "hauteur_colis"),
            ("p_length", "longueur_colis"),
            ("p_width",  "largeur_colis"),
            ("p_weight", "poids_colis"),
        ]:
            el = driver.find_element(By.CSS_SELECTOR, f"input#{field_id}")
            el.clear()
            el.send_keys(str(data[key]))

        calculate_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input#submit"))
        )
        calculate_button.click()

        canvas = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "canvas#palletcanvas"))
        )

        png = canvas.screenshot_as_png
        return send_file(BytesIO(png), mimetype='image/png', as_attachment=False)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
