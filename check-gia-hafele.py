import requests
from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup
import re
import os
from num2words import num2words

def install_dependencies():
    os.system('pip install flask requests beautifulsoup4 num2words')

if __name__ == "__main__":
    install_dependencies()

app = Flask(__name__)

HAFELE_URL = "https://www.hafele.com.vn/hap-live/web/WFS/Haefele-HVN-Site/vi_VN/-/VND/ViewProduct-GetPriceAndAvailabilityInformationPDS?SKU={}&ProductQuantity=1000"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def convert_number_to_words(number):
    return num2words(number, lang='vi')

def get_price(sku):
    cleaned_sku = sku.replace('.', '')  # Loại bỏ dấu chấm
    url = HAFELE_URL.format(cleaned_sku)
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return f"Mã {sku}: Lỗi kết nối hoặc không tìm thấy sản phẩm"
    
    soup = BeautifulSoup(response.text, 'html.parser')
    price_element = soup.find("span", class_="price")
    unit_element = soup.find("span", class_="perUnit")
    
    if not price_element:
        return f"Mã {sku}: Không tìm thấy giá"
    
    price_text = price_element.get_text(strip=True)
    price_numeric = re.sub(r'[^0-9]', '', price_text.split(' ')[0])  # Loại bỏ ký tự không phải số
    
    if len(price_numeric) > 2:
        price_numeric = price_numeric[:-2]  # Bỏ hai chữ số thập phân cuối cùng
    
    price_ex_vat = int(price_numeric)
    price_incl_vat = int(price_ex_vat * 1.1)  # Tính giá đã bao gồm VAT 10%
    
    unit_text = unit_element.get_text(strip=True) if unit_element else "Không xác định"
    
    price_ex_vat_words = convert_number_to_words(price_ex_vat)
    price_incl_vat_words = convert_number_to_words(price_incl_vat)
    
    return (f"Mã {sku} - Giá chưa VAT: {price_ex_vat} VND ({price_ex_vat_words} đồng) - "
            f"Giá đã VAT 10%: {price_incl_vat} VND ({price_incl_vat_words} đồng) - Đơn vị: {unit_text}")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        raw_skus = request.form.get('skus', '')
        skus = [sku.strip() for sku in raw_skus.split(',') if sku.strip()]
        
        results = [get_price(sku) for sku in skus]
        
        return jsonify({'results': results})
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
