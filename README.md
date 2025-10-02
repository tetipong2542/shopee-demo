# Shopee API Integration

ระบบจัดการสินค้าบน Shopee ผ่าน Open API สำหรับอัปเดตราคาและสต็อกสินค้าแบบอัตโนมัติ

## 📋 Features

- ✅ OAuth 2.0 Authentication กับ Shopee
- ✅ จัดการได้หลายร้านค้าในระบบเดียว
- ✅ Web UI สำหรับจัดการร้านค้า
- ✅ อัปเดตราคาสินค้าแบบรายตัว
- ✅ อัปเดตสต็อกสินค้าแบบรายตัว
- ✅ อัปเดตหลายสินค้าพร้อมกัน (Batch Update)
- ✅ Test & Live Environment Support

## 🚀 Quick Start

### Local Development

1. **Clone Repository**
   ```bash
   git clone https://github.com/tetipong2542/shopee-demo.git
   cd shopee-demo
   ```

2. **ติดตั้ง Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **ตั้งค่า Environment Variables**
   ```bash
   cp .env.example .env
   # แก้ไขไฟล์ .env ใส่ค่าต่อไปนี้:
   SHOPEE_PARTNER_ID=your_test_partner_id
   SHOPEE_PARTNER_KEY=your_test_partner_key
   SHOPEE_REDIRECT_URI=http://localhost:5000/auth/callback
   ```

4. **รันระบบ**
   ```bash
   python app.py
   ```

5. **เปิดเว็บไซต์**
   - URL: http://localhost:5000

## 🌐 Railway Deployment

### 1. ปรับใช้บน Railway

1. **Deploy ผ่าน GitHub**
   - เชื่อมต่อ repository นี้กับ Railway
   - Railway จะ deploy อัตโนมัติ

2. **ตั้งค่า Environment Variables ใน Railway**
   ```
   SHOPEE_PARTNER_ID=1189367
   SHOPEE_PARTNER_KEY=shpk49456c6158617a68486d614178776645586846706949545a4f7867416a78
   SHOPEE_REDIRECT_URI=https://your-app-name.railway.app/auth/callback
   FLASK_SECRET_KEY=your-secret-key-here
   ```

3. **ตั้งค่า Redirect URI ใน Shopee Partner Portal**
   - ไปที่: https://partner.test-stable.shopeemobile.com/
   - App Settings → Redirect URLs
   - เพิ่ม: `https://your-app-name.railway.app/auth/callback`

## 📡 API Endpoints

### Authentication
- `GET /auth/login` - เริ่มต้น OAuth Flow
- `GET /auth/callback` - รับ callback หลัง authorize
- `POST /api/refresh-token` - Refresh access token

### Product Management
- `POST /api/update-price` - อัปเดตราคาสินค้า
- `POST /api/update-stock` - อัปเดตสต็อกสินค้า
- `POST /api/batch-update` - อัปเดตหลายสินค้าพร้อมกัน

### Shop Management
- `GET /api/shops` - ดูรายการร้านที่เชื่อมต่อ
- `GET /api/status` - ตรวจสอบสถานะระบบ

## 🔧 ตัวอย่างการใช้ API

### อัปเดตราคาสินค้า
```bash
curl -X POST https://your-app.railway.app/api/update-price \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": 12345678,
    "price": 299.50
  }'
```

### อัปเดตหลายสินค้า (Batch)
```bash
curl -X POST https://your-app.railway.app/api/batch-update \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"item_id": 12345678, "price": 299.50, "stock": 100},
      {"item_id": 87654321, "price": 450.00, "stock": 50}
    ]
  }'
```

## ⚙️ Configuration

### Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `SHOPEE_PARTNER_ID` | ✅ | Partner ID จาก Shopee |
| `SHOPEE_PARTNER_KEY` | ✅ | Partner Key จาก Shopee |
| `SHOPEE_REDIRECT_URI` | ✅ | Callback URL |
| `SHOPEE_BASE_URL` | ❌ | Base URL (default: test environment) |
| `FLASK_SECRET_KEY` | ❌ | Secret key สำหรับ session |

### Test vs Live Environment
```bash
# Test Environment (default)
SHOPEE_BASE_URL=https://partner.test-stable.shopeemobile.com

# Live Environment
SHOPEE_BASE_URL=https://partner.shopeemobile.com
```

## 🔐 Security Notes

- **ห้ามเปิดเผย Partner Key** - เก็บไว้ใน environment variables เท่านั้น
- **Token Storage** - ใน production ควรเก็บ tokens ใน database แทน memory
- **HTTPS** - Production ต้องใช้ HTTPS
- **Rate Limiting** - ระวัง API rate limits ของ Shopee

## 🛠️ Development

### Project Structure
```
shopee-api/
├── app.py              # Flask application
├── templates/
│   └── index.html      # Web UI
├── requirements.txt    # Python dependencies
├── railway.json       # Railway deployment config
├── .env              # Environment variables (local)
├── .gitignore        # Git ignore file
└── README.md         # This file
```

### Dependencies
- Flask 3.0.0 - Web framework
- requests 2.31.0 - HTTP client
- python-dotenv 1.0.0 - Environment variables

## 📝 TODO

- [ ] Database integration (PostgreSQL/MySQL)
- [ ] Token refresh automation
- [ ] Logging system
- [ ] Rate limiting middleware
- [ ] Product list display
- [ ] Webhook support
- [ ] Docker support

## 🤝 Contributing

1. Fork this repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is MIT Licensed

## 🆘 Support

ถ้ามีปัญหา:
1. Check logs ใน Railway dashboard
2. ตรวจสอบ environment variables
3. ตรวจสอบ Shopee Partner ID/Key
4. ตรวจสอบ Redirect URI settings

---

Made with ❤️ for Shopee Sellers