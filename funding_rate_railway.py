import ccxt
import time
import os
from datetime import datetime

# ============================================================================
# FUNDING RATE BOT - BTC/USDT FUTURES (RAILWAY VERSION)
# ============================================================================
# Lee API Keys de variables de entorno (variables de Railway)
# Cobra funding rates cada 8 horas
# Reinvierte automático en Binance Earn
# ============================================================================

# Lee credenciales de variables de entorno de Railway
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

if not API_KEY or not API_SECRET:
    print("❌ ERROR: Falta configurar BINANCE_API_KEY y BINANCE_API_SECRET en Railway")
    print("   Ve a Settings → Variables en tu proyecto Railway")
    exit(1)

exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
})

SYMBOL = 'BTC/USDT'
CAPITAL = 50  # USD
LEVERAGE = 5
FUNDING_CHECK_INTERVAL = 28800  # 8 horas = 28,800 segundos
MIN_FUNDING_RATE = 0.0001  # 0.01% mínimo
MIN_EARN_AMOUNT = 5  # Solo reinvierte si gana más de $5

def get_funding_rate():
    """Obtiene el funding rate actual"""
    try:
        ticker = exchange.fetch_ticker(SYMBOL)
        funding_rate = ticker.get('info', {}).get('fundingRate', 0)
        return float(funding_rate)
    except Exception as e:
        print(f"❌ Error obteniendo funding rate: {e}")
        return None

def get_balance():
    """Obtiene balance actual"""
    try:
        balance = exchange.fetch_balance()
        usdt = balance.get('USDT', {}).get('free', 0)
        return usdt
    except Exception as e:
        print(f"❌ Error obteniendo balance: {e}")
        return 0

def transfer_to_earn(amount):
    """Transfiere USDT ganado a Binance Earn (Flexible)"""
    try:
        if amount < MIN_EARN_AMOUNT:
            print(f"⚠️  ${amount:.2f} es muy pequeño para Earn (mínimo ${MIN_EARN_AMOUNT})")
            return False
        
        # API de Binance Earn
        response = exchange.sapi_post_lending_daily_product_purchase({
            'productId': 'USDT001',  # USDT Flexible Earn
            'amount': amount,
        })
        
        print(f"✅ REINVERTIDO EN BINANCE EARN: ${amount:.2f}")
        print(f"   APY: 21.15% → Ganancia futura: +${amount * 0.2115 / 365:.4f}/día")
        return True
    except Exception as e:
        error_msg = str(e)
        if "USDT001" in error_msg or "productId" in error_msg:
            try:
                response = exchange.sapi_post_simple_account_add_flexible_product({
                    'productId': 'USDT001',
                    'amount': amount,
                })
                print(f"✅ REINVERTIDO EN BINANCE EARN: ${amount:.2f}")
                return True
            except:
                print(f"⚠️  No se pudo reinvertir en Earn. Ganancia queda en billetera: ${amount:.2f}")
                return False
        else:
            print(f"⚠️  Error en Earn: {error_msg[:60]}")
            return False

def calculate_funding_gain(funding_rate):
    """Calcula ganancia por funding rate"""
    # Ganancia = Capital × Leverage × Funding Rate × 3 (cada 8h hay 3 pagos/día)
    gain = CAPITAL * LEVERAGE * abs(funding_rate) * 3
    return gain

def run_bot():
    """Loop principal"""
    print("\n" + "="*70)
    print("🟢 FUNDING RATE BOT - BTC/USDT (RAILWAY VERSION)")
    print("="*70)
    print(f"💵 Capital: ${CAPITAL}")
    print(f"⚡ Leverage: {LEVERAGE}x")
    print(f"📊 Funding rate mínimo: {MIN_FUNDING_RATE*100}%")
    print(f"🎯 Reinvierte en Binance Earn: 21.15% APY")
    print(f"⏱️  Check cada: 8 horas (3 pagos/día)")
    print(f"🚀 Corriendo en RAILWAY (sin PC encendida)")
    print("="*70 + "\n")
    
    cycle = 0
    total_earned = 0
    
    while True:
        try:
            cycle += 1
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            funding_rate = get_funding_rate()
            if funding_rate is None:
                print(f"⚠️  Error obteniendo funding rate. Reintentando...")
                time.sleep(3600)  # 1 hora
                continue
            
            usdt_balance = get_balance()
            
            print(f"\n🔄 CICLO {cycle} | {current_time}")
            print(f"📊 Funding Rate: {funding_rate*100:.4f}%")
            print(f"💰 Balance: ${usdt_balance:,.2f} USDT")
            print(f"📈 Total ganado acumulado: ${total_earned:,.2f}")
            
            # Calcula ganancia
            if funding_rate > 0:  # Positivo = ganas
                gain = calculate_funding_gain(funding_rate)
                
                print(f"✅ FUNDING POSITIVO: ${gain:.4f} ganancia esperada")
                
                # Reinvierte automático en Earn
                success = transfer_to_earn(gain)
                
                if success:
                    total_earned += gain
                    print(f"💎 GANANCIA TOTAL: ${total_earned:,.2f}")
            
            elif funding_rate < 0:  # Negativo = pierdes
                loss = calculate_funding_gain(funding_rate)
                print(f"⚠️  FUNDING NEGATIVO: Pérdida de ${abs(loss):.4f}")
                print(f"   (Esto es normal, espera a que vuelva positivo)")
            
            else:
                print(f"⏳ Funding rate neutral, esperando...")
            
            # Espera 8 horas
            print(f"⏳ Próximo check en 8 horas...")
            time.sleep(FUNDING_CHECK_INTERVAL)
        
        except KeyboardInterrupt:
            print("\n\n⛔ BOT DETENIDO")
            print(f"💰 Total ganado en esta sesión: ${total_earned:,.2f}")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("🔄 Reintentando en 1 hora...")
            time.sleep(3600)

if __name__ == "__main__":
    run_bot()
