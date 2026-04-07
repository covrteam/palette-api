from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright
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

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_default_timeout(60000)

            page.goto("https://www.onpallet.com/fr/calculateur-de-palettes",
                      wait_until="domcontentloaded")

            # Remplir les champs colis
            page.fill("input#p_width",  str(data['largeur_colis']))
            page.fill("input#p_length", str(data['longueur_colis']))
            page.fill("input#p_height", str(data['hauteur_colis']))
            page.fill("input#p_weight", str(data['poids_colis']))

            # Ouvrir le dropdown Bootstrap et cliquer Custom
            page.click("button#palletselect")
            page.wait_for_selector("a#ps_palX", state="visible")
            page.click("a#ps_palX")

            # Remplir dimensions palette directement
            page.fill("input#ps_custW", str(data['largeur_palette']))
            page.fill("input#ps_custL", str(data['longueur_palette']))

            # Calculer
            page.click("input#submit")

            # Attendre le canvas
            page.wait_for_selector("canvas#palletcanvas", state="visible", timeout=60000)
            page.wait_for_timeout(2000)

            png = page.locator("canvas#palletcanvas").screenshot()
            browser.close()

            return send_file(BytesIO(png), mimetype='image/png', as_attachment=False)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
