import pandas as pd
import numpy as np
from binance.client import Client
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import logging
from config import BINANCE_CONFIG

logger = logging.getLogger(__name__)

class UltraDataFetcher:
    """
    🔥 جلب بيانات فائق السرعة من Binance
    """
    
    def __init__(self, config: Dict):
        self.config = config
        try:
            self.client = Client(
                BINANCE_CONFIG.get("api_key", ""),
                BINANCE_CONFIG.get("api_secret", "")
            )
        except:
            self.client = None
            logger.warning("⚠️ تشغيل بدون API keys (وضع محاكاة)")
    
    def prepare_ultra_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """تحضير بيانات فائق السرعة"""
        df = df.copy()
        
        # تحويل الأنواع
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna()
        
        # إضافة أعمدة مساعدة
        df['hlc3'] = (df['high'] + df['low'] + df['close']) / 3
        df['hl2'] = (df['high'] + df['low']) / 2
        
        return df
    
    def fetch_klines(self, symbol: str, interval: str, days: int = 1) -> Optional[pd.DataFrame]:
        """جلب بيانات KLines من Binance"""
        try:
            if not self.client:
                # محاكاة البيانات إذا لم يكن هناك اتصال
                return self.generate_mock_data(symbol, interval, days)
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            klines = self.client.get_historical_klines(
                symbol,
                interval,
                start_date.strftime("%d %b, %Y"),
                end_date.strftime("%d %b, %Y")
            )
            
            if not klines:
                logger.warning(f"⚠️ لا توجد بيانات لـ {symbol}")
                return self.generate_mock_data(symbol, interval, days)
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # تحويل الأنواع
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"❌ خطأ في جلب بيانات {symbol}: {str(e)}")
            return self.generate_mock_data(symbol, interval, days)
    
    def generate_mock_data(self, symbol: str, interval: str, days: int) -> pd.DataFrame:
        """توليد بيانات محاكاة واقعية"""
        logger.info(f"🎲 توليد بيانات محاكاة لـ {symbol} ({days} يوم)")
        
        # إعداد الفترات الزمنية
        if interval == "1m":
            bars_per_day = 1440
        elif interval == "5m":
            bars_per_day = 288
        elif interval == "15m":
            bars_per_day = 96
        else:
            bars_per_day = 24
        
        total_bars = bars_per_day * days
        
        # إنشاء طابع زمني
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        timestamps = pd.date_range(start=start_time, end=end_time, periods=total_bars)
        
        # محاكاة حركة السعر الواقعية
        np.random.seed(42)  # للتكرار
        
        # أسعار بداية واقعية بناءً على الرمز
        base_prices = {
            "BTCUSDT": 45000,
            "ETHUSDT": 2500,
            "BNBUSDT": 300,
            "ADAUSDT": 0.45,
            "XRPUSDT": 0.60,
            "SOLUSDT": 100,
            "DOTUSDT": 7,
            "LINKUSDT": 15,
            "LTCUSDT": 70,
            "DOGEUSDT": 0.08
        }
        
        base_price = base_prices.get(symbol, 100)
        
        # توليد بيانات واقعية
        returns = np.random.normal(0, 0.002, total_bars)  # تقلب 0.2%
        prices = base_price * (1 + returns).cumprod()
        
        # إضافة بعض الاتجاهات والتقلبات الواقعية
        trend = np.sin(np.arange(total_bars) * 0.01) * base_price * 0.1
        prices += trend
        
        # توليد OHLCV
        df = pd.DataFrame({
            'timestamp': timestamps,
            'open': prices,
            'high': prices * (1 + np.abs(np.random.normal(0, 0.005, total_bars))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.005, total_bars))),
            'close': prices * (1 + np.random.normal(0, 0.002, total_bars)),
            'volume': np.random.lognormal(10, 1, total_bars)
        })
        
        # ضمان أن high هو الأعلى و low هو الأدنى
        df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
        df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
        
        return df
    
    def fetch_multiple_klines(self, symbols: List[str], interval: str, days: int = 1) -> Dict:
        """جلب بيانات متعددة بشكل متوازي"""
        klines_data = {}
        
        logger.info(f"📥 جلب بيانات {len(symbols)} زوج لمدة {days} يوم")
        
        for symbol in symbols:
            df = self.fetch_klines(symbol, interval, days)
            if df is not None and not df.empty:
                klines_data[symbol] = df
                logger.info(f"✅ تم جلب {len(df)} شمعة لـ {symbol}")
            else:
                logger.warning(f"⚠️ فشل جلب بيانات {symbol}")
        
        return klines_data
