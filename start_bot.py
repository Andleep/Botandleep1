#!/usr/bin/env python3
"""
🚀 ملف تشغيل البوت على Render
"""

import os
import sys
import logging
from main_bot import UltraFastTradingBot, SUPER_CONFIG
from data_fetcher import UltraDataFetcher

# إعداد logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('render_bot.log')
    ]
)

logger = logging.getLogger(__name__)

def load_render_config():
    """تحميل الإعدادات من متغيرات البيئة في Render"""
    config = SUPER_CONFIG.copy()
    
    # تحديث الإعدادات من environment variables
    config["initial_balance"] = float(os.getenv("INITIAL_BALANCE", 10.0))
    config["timeframe"] = os.getenv("TIME_FRAME", "1m")
    config["simulation_days"] = int(os.getenv("SIMULATION_DAYS", 7))
    config["base_risk"] = float(os.getenv("BASE_RISK", 0.03))
    
    # معالجة الأزواج
    pairs_str = os.getenv("SELECTED_PAIRS", "BTCUSDT,ETHUSDT,BNBUSDT,ADAUSDT,XRPUSDT")
    config["selected_pairs"] = [p.strip() for p in pairs_str.split(",")]
    
    logger.info(f"🎯 الإعدادات المحملة: {len(config['selected_pairs'])} أزواج | رأس المال: ${config['initial_balance']}")
    
    return config

def run_bot_on_render():
    """تشغيل البوت على بيئة Render"""
    try:
        logger.info("🚀 بدء تشغيل البوت على Render...")
        
        # تحميل الإعدادات
        config = load_render_config()
        
        # إنشاء البوت
        bot = UltraFastTradingBot(config)
        
        # جلب البيانات
        data_fetcher = UltraDataFetcher(config)
        klines_data = data_fetcher.fetch_multiple_klines(
            config["selected_pairs"], 
            config["timeframe"], 
            days=config["simulation_days"]
        )
        
        if not klines_data:
            logger.error("❌ فشل في جلب بيانات السوق")
            return False
        
        logger.info(f"✅ تم جلب بيانات {len(klines_data)} زوج بنجاح")
        
        # تشغيل المحاكاة
        results = bot.run_ultra_simulation(
            klines_data, 
            config["timeframe"],
            days=config["simulation_days"]
        )
        
        # عرض النتائج
        print("\n" + "="*70)
        print("🚀 نتائج البوت التداولي الفائق على Render")
        print("="*70)
        print(f"📊 إجمالي الصفقات: {results['total_trades']}")
        print(f"💰 الربح الإجمالي: ${results['total_profit']:.2f} ({results['profit_percentage']:.2f}%)")
        print(f"🎯 معدل النجاح: {results['win_rate']:.1f}%")
        print(f"💎 الرصيد النهائي: ${results['final_balance']:.2f}")
        print(f"🔥 الأرباح المتراكمة: ${results['metrics']['compounded_profits']:.2f}")
        print("="*70)
        
        # تحليل الإشارات
        if results['signal_analysis']:
            print("\n📈 تحليل أنواع الإشارات:")
            for signal_type, analysis in results['signal_analysis'].items():
                win_rate = (analysis['wins'] / analysis['count'] * 100) if analysis['count'] > 0 else 0
                avg_profit = analysis['profits'] / analysis['count'] if analysis['count'] > 0 else 0
                print(f"   {signal_type}: {analysis['count']} صفقة | نجاح: {win_rate:.1f}% | متوسط الربح: ${avg_profit:.4f}")
        
        logger.info("✅ اكتمل تشغيل البوت بنجاح على Render")
        return True
        
    except Exception as e:
        logger.error(f"❌ خطأ في التشغيل على Render: {str(e)}")
        return False

if __name__ == "__main__":
    # تشغيل البوت
    success = run_bot_on_render()
    
    if success:
        print("\n🎉 البوت اكتمل بنجاح! تحقق من السجلات للتفاصيل الكاملة.")
        sys.exit(0)
    else:
        print("\n❌ فشل تشغيل البوت. تحقق من السجلات للتفاصيل.")
        sys.exit(1)
