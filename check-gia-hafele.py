import requests
from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup
import re
import os
from num2words import num2words

# Hàm này chỉ chạy một lần khi khởi động ứng dụng
def install_dependencies():
    # Sử dụng os.system để chạy lệnh pip, đảm bảo các thư viện cần thiết được cài đặt
    os.system('pip install flask requests beautifulsoup4 num2words')

# Đảm bảo các thư viện được cài đặt trước khi khởi động ứng dụng Flask
if __name__ == "__main__":
    install_dependencies()

app = Flask(__name__)

# URL cơ bản để tra cứu giá sản phẩm Hafele
HAFELE_URL = "https://www.hafele.com.vn/hap-live/web/WFS/Haefele-HVN-Site/vi_VN/-/VND/ViewProduct-GetPriceAndAvailabilityInformationPDS?SKU={}&ProductQuantity=1000"
# Tiêu đề HTTP để giả lập trình duyệt, tránh bị chặn bởi máy chủ
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# Hàm chuyển đổi số thành chữ tiếng Việt
def convert_number_to_words(number):
    return num2words(number, lang='vi')

# Hàm chính để lấy giá sản phẩm từ trang web Hafele
def get_price(sku):
    # Loại bỏ dấu chấm trong SKU để phù hợp với định dạng URL
    cleaned_sku = sku.replace('.', '')
    # Tạo URL hoàn chỉnh để truy vấn giá
    url = HAFELE_URL.format(cleaned_sku)
    
    try:
        # Gửi yêu cầu GET đến URL và đặt thời gian chờ là 10 giây
        response = requests.get(url, headers=HEADERS, timeout=10)
        # Kiểm tra mã trạng thái HTTP, nếu có lỗi sẽ ném ngoại lệ
        response.raise_for_status()
    except requests.RequestException:
        # Xử lý lỗi kết nối hoặc không tìm thấy sản phẩm
        return f"Mã {sku}: Lỗi kết nối hoặc không tìm thấy sản phẩm"
    
    # Phân tích cú pháp HTML của trang web bằng BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    # Tìm thẻ span có class 'price' chứa thông tin giá
    price_element = soup.find("span", class_="price")
    # Tìm thẻ span có class 'perUnit' chứa thông tin đơn vị
    unit_element = soup.find("span", class_="perUnit")
    
    # Nếu không tìm thấy phần tử giá, trả về thông báo lỗi
    if not price_element:
        return f"Mã {sku}: Không tìm thấy giá"
    
    # Lấy văn bản từ phần tử giá và loại bỏ khoảng trắng
    price_text = price_element.get_text(strip=True)
    # Sử dụng biểu thức chính quy để chỉ lấy các chữ số từ văn bản giá
    price_numeric = re.sub(r'[^0-9]', '', price_text.split(' ')[0])
    
    # Loại bỏ hai chữ số thập phân cuối cùng nếu có, vì trang web Hafele thường hiển thị giá kèm 2 số 00
    if len(price_numeric) > 2:
        price_numeric = price_numeric[:-2]
    
    # Chuyển đổi giá sang số nguyên
    price_ex_vat = int(price_numeric)
    # Tính giá đã bao gồm VAT 10%
    price_incl_vat = int(price_ex_vat * 1.1)
    
    # Lấy văn bản đơn vị, nếu không có thì mặc định là "Không xác định"
    unit_text = unit_element.get_text(strip=True) if unit_element else "Không xác định"
    
    # Chuyển đổi giá chưa VAT và đã VAT sang dạng chữ
    price_ex_vat_words = convert_number_to_words(price_ex_vat)
    price_incl_vat_words = convert_number_to_words(price_incl_vat)
    
    # Trả về chuỗi kết quả đã định dạng
    return (f"Mã {sku} - Giá chưa VAT: {price_ex_vat} VND ({price_ex_vat_words} đồng) - "
            f"Giá đã VAT 10%: {price_incl_vat} VND ({price_incl_vat_words} đồng) - Đơn vị: {unit_text}")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        raw_skus = request.form.get('skus', '')
        # Chia chuỗi SKU bằng ký tự xuống dòng và loại bỏ khoảng trắng
        # Lọc bỏ các dòng trống
        skus = [sku.strip() for sku in raw_skus.split('\n') if sku.strip()]
        
        # Lấy giá cho từng SKU và lưu vào danh sách results
        results = [get_price(sku) for sku in skus]
        
        # Trả về kết quả dưới dạng JSON
        return jsonify({'results': results})
    
    # Nếu là yêu cầu GET, hiển thị trang HTML
    return render_template('index.html')

if __name__ == '__main__':
    # Chạy ứng dụng Flask ở chế độ debug
    app.run(debug=True)
