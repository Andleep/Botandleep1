import pandas as pd
import numpy as np
import talib
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class SuperStrategyEngine:
    """
    🔥 محرك استراتيجية تداول فائق السرعة
    يجمع بين مؤشرات Heikin Ashi, Renko, EMA, ATR, RSI
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.setup_type = config.get("setup_type", "Open/Close")
        self.trend_type = config.get("trend_type", True)
        
    def calculate_heikin_ashi(self, df: pd.DataFrame) -> pd.DataFrame:
        """حساب شموع Heikin Ashi"""
        df = df.copy()
        
        # شموع Heikin Ashi
        df['ha_close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        df['ha_open'] = (df['open'].shift(1) + df['close'].shift(1)) / 2
        df['ha_open'].iloc[0] = (df['open'].iloc[0] + df['close'].iloc[0]) / 2
        
        df['ha_high'] = df[['high', 'ha_open', 'ha_close']].max(axis=1)
        df['ha_low'] = df[['low', 'ha_open', 'ha_close']].min(axis=1)
        
        return df
    
    def calculate_renko_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """حساب مؤشرات Renko"""
        df = df.copy()
        
        # مؤشرات EMA لـ Renko
        ema1_length = self.config.get("ema1_length", 2)
        ema2_length = self.config.get("ema2_length", 10)
        
        df['renko_ema1'] = talib.EMA(df['close'], ema1_length)
        df['renko_ema2'] = talib.EMA(df['close'], ema2_length)
        
        # إشارات Renko
        df['renko_buy'] = (df['renko_ema1'] > df['renko_ema2']) & (df['renko_ema1'].shift(1) <= df['renko_ema2'].shift(1))
        df['renko_sell'] = (df['renko_ema1'] < df['renko_ema2']) & (df['renko_ema1'].shift(1) >= df['renko_ema2'].shift(1))
        
        return df
    
    def calculate_ema_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """حساب مؤشرات EMA المتعددة"""
        df = df.copy()
        
        # EMAs سريعة
        df["ema_5"] = talib.EMA(df["close"], 5)
        df["ema_10"] = talib.EMA(df["close"], 10)
        df["ema_20"] = talib.EMA(df["close"], 20)
        
        # EMAs متوسطة
        df["ema_48"] = talib.EMA(df["close"], 48)
        df["ema_21"] = talib.EMA(df["close"], 21)
        
        return df
    
    def calculate_rsi_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """حساب مؤشرات RSI"""
        df = df.copy()
        
        # RSI سريع وبطيء
        df["rsi_6"] = talib.RSI(df["close"], 6)
        df["rsi_14"] = talib.RSI(df["close"], 14)
        df["rsi_7"] = talib.RSI(df["close"], 7)
        
        return df
    
    def calculate_macd_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """حساب مؤشر MACD"""
        df = df.copy()
        
        df["macd"], df["macd_signal"], df["macd_hist"] = talib.MACD(
            df["close"], 
            fastperiod=6, 
            slowperiod=13, 
            signalperiod=3
        )
        
        return df
    
    def calculate_stochastic_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """حساب مؤشر ستوكاستك"""
        df = df.copy()
        
        df["stoch_k"], df["stoch_d"] = talib.STOCH(
            df["high"], df["low"], df["close"],
            fastk_period=5, slowk_period=3, slowd_period=0
        )
        
        return df
    
    def calculate_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """حساب بولنجر باند"""
        df = df.copy()
        
        df["bb_upper"], df["bb_middle"], df["bb_lower"] = talib.BBANDS(
            df["close"], timeperiod=10, nbdevup=1.5, nbdevdn=1.5
        )
        
        return df
    
    def calculate_atr_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """حساب مؤشر ATR"""
        df = df.copy()
        
        df["atr_5"] = talib.ATR(df["high"], df["low"], df["close"], 5)
        df["atr_14"] = talib.ATR(df["high"], df["low"], df["close"], 14)
        df["atr_20"] = talib.ATR(df["high"], df["low"], df["close"], 20)
        
        return df
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """حساب جميع المؤشرات"""
        df = self.calculate_heikin_ashi(df)
        df = self.calculate_renko_indicators(df)
        df = self.calculate_ema_indicators(df)
        df = self.calculate_rsi_indicators(df)
        df = self.calculate_macd_indicators(df)
        df = self.calculate_stochastic_indicators(df)
        df = self.calculate_bollinger_bands(df)
        df = self.calculate_atr_indicators(df)
        
        # 🔥 توليد الإشارات النهائية
        df = self.generate_trading_signals(df)
        
        return df
    
    def generate_trading_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """توليد إشارات التداول بناءً على جميع المؤشرات"""
        df = df.copy()
        
        # 1. إشارات Heikin Ashi (Open/Close)
        df['ha_buy'] = (df['ha_close'] > df['ha_open']) & (df['ha_close'].shift(1) <= df['ha_open'].shift(1))
        df['ha_sell'] = (df['ha_close'] < df['ha_open']) & (df['ha_close'].shift(1) >= df['ha_open'].shift(1))
        
        # 2. إشارات Renko
        df['renko_buy_signal'] = df['renko_buy']
        df['renko_sell_signal'] = df['renko_sell']
        
        # 3. إشارات EMA
        df['ema_buy'] = (df['ema_5'] > df['ema_10']) & (df['ema_5'].shift(1) <= df['ema_10'].shift(1))
        df['ema_sell'] = (df['ema_5'] < df['ema_10']) & (df['ema_5'].shift(1) >= df['ema_10'].shift(1))
        
        # 4. إشارات RSI
        df['rsi_oversold'] = df['rsi_6'] < 25
        df['rsi_overbought'] = df['rsi_6'] > 75
        
        # 5. إشارات MACD
        df['macd_buy'] = (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))
        df['macd_sell'] = (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1))
        
        # 6. إشارات ستوكاستك
        df['stoch_oversold'] = (df['stoch_k'] < 20) & (df['stoch_d'] < 20)
        df['stoch_overbought'] = (df['stoch_k'] > 80) & (df['stoch_d'] > 80)
        
        # 7. إشارات بولنجر باند
        df['bb_buy'] = df['close'] < df['bb_lower']
        df['bb_sell'] = df['close'] > df['bb_upper']
        
        # 🔥 الإشارات الفورية فائقة السرعة
        df['instant_buy'] = (
            (df['rsi_6'] < 25) & 
            (df['close'] < df['bb_lower']) & 
            (df['macd_hist'] > 0) &
            (df['ema_5'] > df['ema_10'])
        )
        
        df['instant_sell'] = (
            (df['rsi_6'] > 75) & 
            (df['close'] > df['bb_upper']) & 
            (df['macd_hist'] < 0) &
            (df['ema_5'] < df['ema_10'])
        )
        
        # إشارات الزخم الفوري
        df['momentum_buy'] = (df['close'] > df['ema_5']).rolling(3).sum() >= 2
        df['momentum_sell'] = (df['close'] < df['ema_5']).rolling(3).sum() >= 2
        
        # إشارات الحجم الفوري
        df['volume_spike'] = (df['volume'] / df['volume'].rolling(10).mean()) > 1.5
        
        return df
    
    def ultra_fast_decision(self, df: pd.DataFrame, idx: int, symbol: str) -> Dict:
        """🔥 قرار تداول فائق السرعة يجمع جميع المؤشرات"""
        if idx < 20:
            return {"signal": "HOLD", "confidence": 0, "reason": "بيانات غير كافية"}
        
        row = df.iloc[idx]
        
        # 🔥 نظام التصويت الذكي المتعدد
        buy_score = 0
        sell_score = 0
        signal_details = []
        
        # 1. إشارات Heikin Ashi (وزن عالي)
        if row['ha_buy']:
            buy_score += 3
            signal_details.append("HA_BUY")
        if row['ha_sell']:
            sell_score += 3
            signal_details.append("HA_SELL")
        
        # 2. إشارات Renko (وزن عالي)
        if row['renko_buy_signal']:
            buy_score += 3
            signal_details.append("RENKO_BUY")
        if row['renko_sell_signal']:
            sell_score += 3
            signal_details.append("RENKO_SELL")
        
        # 3. إشارات EMA (وزن متوسط)
        if row['ema_buy']:
            buy_score += 2
            signal_details.append("EMA_BUY")
        if row['ema_sell']:
            sell_score += 2
            signal_details.append("EMA_SELL")
        
        # 4. إشارات RSI (وزن متوسط)
        if row['rsi_oversold']:
            buy_score += 2
            signal_details.append("RSI_OVERSOLD")
        if row['rsi_overbought']:
            sell_score += 2
            signal_details.append("RSI_OVERBOUGHT")
        
        # 5. إشارات MACD (وزن متوسط)
        if row['macd_buy']:
            buy_score += 2
            signal_details.append("MACD_BUY")
        if row['macd_sell']:
            sell_score += 2
            signal_details.append("MACD_SELL")
        
        # 6. إشارات فورية فائقة السرعة (أعلى وزن)
        if row['instant_buy']:
            buy_score += 4
            signal_details.append("INSTANT_BUY")
        if row['instant_sell']:
            sell_score += 4
            signal_details.append("INSTANT_SELL")
        
        # 7. إشارات الزخم (وزن منخفض)
        if row['momentum_buy']:
            buy_score += 1
            signal_details.append("MOMENTUM_BUY")
        if row['momentum_sell']:
            sell_score += 1
            signal_details.append("MOMENTUM_SELL")
        
        # 8. بولنجر باند (وزن متوسط)
        if row['bb_buy']:
            buy_score += 2
            signal_details.append("BB_BUY")
        if row['bb_sell']:
            sell_score += 2
            signal_details.append("BB_SELL")
        
        # 9. ستوكاستك (وزن منخفض)
        if row['stoch_oversold']:
            buy_score += 1
            signal_details.append("STOCH_OVERSOLD")
        if row['stoch_overbought']:
            sell_score += 1
            signal_details.append("STOCH_OVERBOUGHT")
        
        # 10. الحجم (وزن منخفض)
        if row['volume_spike']:
            if buy_score > sell_score:
                buy_score += 1
                signal_details.append("VOLUME_SPIKE_BUY")
            elif sell_score > buy_score:
                sell_score += 1
                signal_details.append("VOLUME_SPIKE_SELL")
        
        # حساب الثقة النهائية
        total_score = buy_score + sell_score
        if total_score == 0:
            return {
                "signal": "HOLD", 
                "confidence": 0, 
                "reason": "لا توجد إشارات قوية",
                "signal_type": "NO_SIGNAL"
            }
        
        buy_ratio = buy_score / total_score
        sell_ratio = sell_score / total_score
        
        confidence = max(buy_ratio, sell_ratio) * 100
        
        # 🔥 قرار فائق السرعة مع عتبات ذكية
        if buy_ratio >= 0.65 and confidence >= 65:
            return {
                "signal": "BUY",
                "confidence": confidence,
                "reason": f"🔥 إشارات شراء متعددة ({buy_score}/{total_score}) - {', '.join(signal_details)}",
                "signal_type": "MULTI_SIGNAL_BUY",
                "score_details": {"buy": buy_score, "sell": sell_score, "signals": signal_details}
            }
        elif sell_ratio >= 0.65 and confidence >= 65:
            return {
                "signal": "SELL", 
                "confidence": confidence,
                "reason": f"🔥 إشارات بيع متعددة ({sell_score}/{total_score}) - {', '.join(signal_details)}",
                "signal_type": "MULTI_SIGNAL_SELL",
                "score_details": {"buy": buy_score, "sell": sell_score, "signals": signal_details}
            }
        else:
            return {
                "signal": "HOLD",
                "confidence": confidence,
                "reason": f"إشارات غير حاسمة (شراء: {buy_score}, بيع: {sell_score})",
                "signal_type": "WEAK_SIGNAL",
                "score_details": {"buy": buy_score, "sell": sell_score, "signals": signal_details}
            }
