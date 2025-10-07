import numpy as np
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class QuantumRiskManager:
    """
    🔥 نظام إدارة مخاطر كمومي مع ربح تراكمي فوري
    """
    
    def __init__(self, config: Dict):
        self.config = config
        
    def calculate_position_size(self, balance: float, confidence: float, 
                              symbol: str, metrics: Dict) -> Tuple[float, float, float]:
        """🔥 حساب حجم المركز مع إدارة مخاطر متقدمة"""
        
        # قاعدة خطر ديناميكية
        base_risk = self.config.get("base_risk", 0.03)  # 3% أساسي
        
        # 🔥 تعديل ذكي بناءً على الأداء
        if metrics.get('consecutive_wins', 0) >= 3:
            base_risk *= 1.8  # زيادة كبيرة بعد 3 انتصارات متتالية
            logger.info(f"🎯 زيادة المخاطرة بعد 3 انتصارات متتالية: {base_risk*100:.1f}%")
        elif metrics.get('consecutive_wins', 0) >= 2:
            base_risk *= 1.4  # زيادة متوسطة بعد انتصارين
        elif metrics.get('consecutive_losses', 0) >= 2:
            base_risk *= 0.6  # تقليل كبير بعد خسارتين متتاليتين
            logger.warning(f"⚠️ تقليل المخاطرة بعد خسارتين متتاليتين: {base_risk*100:.1f}%")
        elif metrics.get('consecutive_losses', 0) >= 1:
            base_risk *= 0.8  # تقليل طفيف بعد خسارة
            
        # تعديل حسب الثقة
        confidence_factor = confidence / 100.0
        risk_adjusted = base_risk * confidence_factor
        
        # 🔥 حدود ذكية
        max_risk = self.config.get("max_risk", 0.08)
        min_risk = self.config.get("min_risk", 0.015)
        final_risk = np.clip(risk_adjusted, min_risk, max_risk)
        
        # حساب حجم المركز
        position_size = balance * final_risk
        
        # 🔥 حدود حجم الصفقة الذكية
        min_trade = self.config.get("min_trade", 0.80)
        max_trade = self.config.get("max_trade", 4.00)
        position_size = np.clip(position_size, min_trade, max_trade)
        
        # 🔥 وقف خسارة وجني أرباح ديناميكي
        stop_loss_pct = self.config.get("stop_loss_pct", 0.012)  # 1.2%
        take_profit_pct = self.config.get("take_profit_pct", 0.008)  # 0.8%
        
        # تعديل بناءً على الثقة
        if confidence > 80:
            take_profit_pct *= 1.3  # زيادة جني الأرباح للثقة العالية
        elif confidence > 70:
            take_profit_pct *= 1.15  # زيادة متوسطة
        
        # 🔥 ضمان نسبة ربح 2:1
        if take_profit_pct < (stop_loss_pct * 2):
            take_profit_pct = stop_loss_pct * 2
        
        logger.debug(f"💰 إدارة مخاطرة {symbol}: حجم ${position_size:.2f}, وقف {stop_loss_pct*100:.1f}%, جني {take_profit_pct*100:.1f}%")
        
        return position_size, stop_loss_pct, take_profit_pct
    
    def apply_instant_profit_compounding(self, profit: float, metrics: Dict, 
                                       bot, position_data: Dict):
        """🔥 تطبيق ربح تراكمي فوري مع تحديث فوري للرصيد"""
        
        if profit > 0:
            # 🔥 التسجيل الدقيق
            old_balance = bot.balance
            bot.balance += profit  # الإضافة الفورية للرصيد
            
            # 🔥 تحديث المقاييس
            metrics['total_profit'] += profit
            metrics['daily_profit'] += profit
            metrics['winning_trades'] += 1
            metrics['compounded_profits'] += profit
            metrics['consecutive_wins'] += 1
            metrics['consecutive_losses'] = 0
            metrics['current_streak'] += 1
            metrics['max_streak'] = max(metrics['max_streak'], metrics['current_streak'])
            
            profit_pct = (profit / position_data["amount"]) * 100
            
            logger.info(f"💰 ربح تراكمي فوري: +${profit:.4f} ({profit_pct:.2f}%) | "
                       f"الرصيد: {old_balance:.2f} → {bot.balance:.2f} | "
                       f"تتابع انتصارات: {metrics['consecutive_wins']}")
            
        else:
            loss = abs(profit)
            loss_pct = (loss / position_data["amount"]) * 100
            
            metrics['losing_trades'] += 1
            metrics['consecutive_losses'] += 1
            metrics['consecutive_wins'] = 0
            metrics['current_streak'] = 0
            
            logger.warning(f"📉 خسارة: -${loss:.4f} ({loss_pct:.2f}%) | "
                          f"تتابع خسائر: {metrics['consecutive_losses']}")
    
    def check_daily_limits(self, metrics: Dict) -> bool:
        """فحص الحدود اليومية"""
        daily_loss_limit = self.config.get("daily_loss_limit", 0.15)
        current_daily_loss = abs(metrics.get('daily_profit', 0)) if metrics.get('daily_profit', 0) < 0 else 0
        
        if current_daily_loss >= (bot.initial_balance * daily_loss_limit):
            logger.error(f"🛑 توقف: تجاوز الحد اليومي للخسارة ({daily_loss_limit*100}%)")
            return False
        
        consecutive_loss_limit = self.config.get("consecutive_loss_limit", 3)
        if metrics.get('consecutive_losses', 0) >= consecutive_loss_limit:
            logger.error(f"🛑 توقف: {consecutive_loss_limit} خسائر متتالية")
            return False
        
        return True
