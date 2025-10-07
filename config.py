import os

# إعدادات Binance
BINANCE_CONFIG = {
    "api_key": os.getenv("BINANCE_API_KEY", ""),
    "api_secret": os.getenv("BINANCE_API_SECRET", "")
}

# 🔥 الإعدادات الفائقة للبوت
SUPER_CONFIG = {
    # 🔥 الإعدادات الأساسية
    "initial_balance": 10.0,
    "selected_pairs": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT"],
    
    # 🔥 إدارة الأموال الفائقة
    "base_risk": 0.03,          # 3% مخاطرة أساسية
    "max_risk": 0.08,           # 8% أقصى مخاطرة
    "min_risk": 0.015,          # 1.5% أدنى مخاطرة
    "min_trade": 0.80,          # 80 سنت حد أدنى
    "max_trade": 4.00,          # 4$ حد أقصى
    
    # 🔥 وقف الخسارة وجني الأرباح
    "stop_loss_pct": 0.012,     # 1.2% وقف خسارة
    "take_profit_pct": 0.008,   # 0.8% جني أرباح
    
    # 🔥 إعدادات التداول الفائق
    "confidence_threshold": 65, # 65% ثقة أدنى
    "timeframe": "1m",          # 1 دقيقة لإطار سريع
    "max_trades_per_day": 500,  # 500 صفقة كحد أقصى
    "simulation_days": 7,       # 7 أيام محاكاة
    
    # 🔥 أنظمة الحماية
    "daily_loss_limit": 0.15,   # 15% أقصى خسارة يومية
    "consecutive_loss_limit": 3,# توقف بعد 3 خسائر متتالية
    
    # 🔥 الربح التراكمي
    "compounding_mode": "INSTANT", # تراكمي فوري
    "risk_multiplier_win": 1.8,    # مضاعفة المخاطرة بعد الربح
    "risk_multiplier_loss": 0.6,   # تقليل المخاطرة بعد الخسارة
    
    # 🔥 إعدادات الاستراتيجية
    "setup_type": "Open/Close",    # Heikin Ashi
    "trend_type": True,           # فلترة الاتجاه
    "ema1_length": 2,             # EMA سريع
    "ema2_length": 10,            # EMA بطيء
    
    # 🔥 المؤشرات
    "enable_heikin_ashi": True,
    "enable_renko": True,
    "enable_ema": True,
    "enable_rsi": True,
    "enable_macd": True,
    "enable_stochastic": True,
    "enable_bollinger": True,
    "enable_atr": True
}
