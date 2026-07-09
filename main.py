"""
INTENTO 9 DINÁMICO - REPLIT VERSION
Bot de trading en vivo con re-entrenamiento automático
Compatible con Binance Futures (Testnet y Live)
"""

import os
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from binance.client import Client
from binance.exceptions import BinanceAPIException
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURACIÓN - REPLIT ENVIRONMENT VARIABLES
# ============================================================================
API_KEY = os.getenv('BINANCE_API_KEY', '')
API_SECRET = os.getenv('BINANCE_API_SECRET', '')
TESTNET = os.getenv('TESTNET', 'False').lower() == 'true'

# Parámetros del bot
SYMBOL = 'BTCUSDT'
LEVERAGE = 5
POSITION_SIZE = 0.001  # BTC
TP_PERCENT = 0.5
SL_PERCENT = 0.5
THRESHOLD = 1.5
LOOKBACK = 100
INTERVAL = '5m'

# ============================================================================
# VALIDACIÓN INICIAL
# ============================================================================
if not API_KEY or not API_SECRET:
    print("❌ ERROR: Falta configurar API_KEY y API_SECRET")
    print("📋 Ve a: Secrets (panel izquierdo) → Agregar secret")
    print("   - Nombre: BINANCE_API_KEY")
    print("   - Valor: Tu API key de Binance")
    print("   - Nombre: BINANCE_API_SECRET")
    print("   - Valor: Tu API secret de Binance")
    exit(1)

# ============================================================================
# CLIENTE BINANCE
# ============================================================================
if TESTNET:
    client = Client(API_KEY, API_SECRET, testnet=True)
    print("🧪 Modo TESTNET activado (sin dinero real)")
else:
    client = Client(API_KEY, API_SECRET)
    print("🚀 Modo LIVE activado (dinero real)")

# ============================================================================
# FUNCIONES DE DATOS
# ============================================================================

def obtener_datos_klines(symbol, interval, limit=100):
    """Obtiene velas históricas de Binance"""
    try:
        klines = client.futures_klines(
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        df = pd.DataFrame(klines, columns=[
            'time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'
        ])
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        df[['open', 'high', 'low', 'close', 'volume']] = \
            df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        return df
    except Exception as e:
        print(f"❌ Error obteniendo datos: {e}")
        return None

def calcular_features(df):
    """Calcula características técnicas"""
    df['sma_10'] = df['close'].rolling(10).mean()
    df['sma_20'] = df['close'].rolling(20).mean()
    df['sma_50'] = df['close'].rolling(50).mean()
    
    df['rsi'] = calcular_rsi(df['close'], 14)
    df['macd'], df['macd_signal'] = calcular_macd(df['close'])
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = calcular_bandas_bollinger(df['close'], 20, 2)
    df['volatility'] = df['close'].rolling(20).std()
    
    return df

def calcular_rsi(close, period=14):
    """RSI indicator"""
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calcular_macd(close, fast=12, slow=26, signal=9):
    """MACD indicator"""
    ema_fast = close.ewm(span=fast).mean()
    ema_slow = close.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal).mean()
    return macd, macd_signal

def calcular_bandas_bollinger(close, period=20, num_std=2):
    """Bollinger Bands"""
    sma = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = sma + (std * num_std)
    lower = sma - (std * num_std)
    return upper, sma, lower

# ============================================================================
# MODELO ML - RANDOM FOREST
# ============================================================================

class ModeloIntento9:
    def __init__(self):
        self.modelo = None
        self.scaler = StandardScaler()
        self.win_rate = 0.5
        self.trades_count = 0
        self.última_reentrenamiento = time.time()
        
    def entrenar(self, df):
        """Entrena el modelo con datos históricos"""
        df = df.dropna()
        
        # Features
        features = ['sma_10', 'sma_20', 'sma_50', 'rsi', 'macd', 'bb_upper', 'bb_lower', 'volatility']
        X = df[features].values
        
        # Target: 1 si el precio sube en la próxima vela, 0 si baja
        y = (df['close'].shift(-1) > df['close']).astype(int).values[:-1]
        X = X[:-1]
        
        if len(X) < 20:
            print("⚠️  Datos insuficientes para entrenar")
            return False
        
        try:
            X_scaled = self.scaler.fit_transform(X)
            self.modelo = RandomForestClassifier(
                n_estimators=50,
                max_depth=8,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )
            self.modelo.fit(X_scaled, y)
            print(f"✅ Modelo entrenado con {len(X)} muestras")
            return True
        except Exception as e:
            print(f"❌ Error entrenando modelo: {e}")
            return False
    
    def predecir(self, df):
        """Predice si comprar (1) o no (0)"""
        if self.modelo is None:
            return None
        
        try:
            df = df.dropna()
            features = ['sma_10', 'sma_20', 'sma_50', 'rsi', 'macd', 'bb_upper', 'bb_lower', 'volatility']
            
            X = df[features].iloc[-1:].values
            X_scaled = self.scaler.transform(X)
            
            probabilidad = self.modelo.predict_proba(X_scaled)[0][1]  # Probabilidad de subida
            predicción = self.modelo.predict(X_scaled)[0]
            
            return {
                'señal': predicción,
                'confianza': probabilidad,
                'debería_comprar': probabilidad > THRESHOLD / 100
            }
        except Exception as e:
            print(f"❌ Error prediciendo: {e}")
            return None
    
    def actualizar_win_rate(self, ganancia_realizada):
        """Actualiza el win rate basado en trades ejecutados"""
        self.trades_count += 1
        if ganancia_realizada > 0:
            self.win_rate = (self.win_rate * (self.trades_count - 1) + 1) / self.trades_count
        else:
            self.win_rate = (self.win_rate * (self.trades_count - 1)) / self.trades_count

# ============================================================================
# TRADING
# ============================================================================

class TradingBot:
    def __init__(self):
        self.modelo = ModeloIntento9()
        self.posición_abierta = False
        self.entrada_precio = 0
        self.entrada_cantidad = 0
        self.tp_precio = 0
        self.sl_precio = 0
        self.historial = []
        
    def inicializar(self):
        """Configura leverage y carga datos iniciales"""
        try:
            # Configurar leverage
            client.futures_change_leverage(symbol=SYMBOL, leverage=LEVERAGE)
            print(f"✅ Leverage configurado a {LEVERAGE}x")
            
            # Obtener datos y entrenar modelo
            df = obtener_datos_klines(SYMBOL, INTERVAL, LOOKBACK)
            if df is not None:
                df = calcular_features(df)
                self.modelo.entrenar(df)
                return True
        except Exception as e:
            print(f"❌ Error en inicialización: {e}")
        return False
    
    def obtener_balance(self):
        """Obtiene balance en Futures"""
        try:
            account = client.futures_account()
            return float(account['totalWalletBalance'])
        except Exception as e:
            print(f"❌ Error obteniendo balance: {e}")
            return 0
    
    def abrir_posición(self, precio_actual):
        """Abre una posición LONG"""
        try:
            cantidad = POSITION_SIZE
            
            order = client.futures_create_order(
                symbol=SYMBOL,
                side='BUY',
                type='MARKET',
                quantity=cantidad,
                leverage=LEVERAGE
            )
            
            self.posición_abierta = True
            self.entrada_precio = float(order['avgPrice'])
            self.entrada_cantidad = cantidad
            self.tp_precio = self.entrada_precio * (1 + TP_PERCENT / 100)
            self.sl_precio = self.entrada_precio * (1 - SL_PERCENT / 100)
            
            print(f"\n🟢 COMPRA EJECUTADA")
            print(f"   Precio: ${self.entrada_precio:.2f}")
            print(f"   Cantidad: {cantidad} BTC")
            print(f"   TP: ${self.tp_precio:.2f}")
            print(f"   SL: ${self.sl_precio:.2f}")
            
            return True
        except Exception as e:
            print(f"❌ Error abriendo posición: {e}")
            return False
    
    def cerrar_posición(self, razón=""):
        """Cierra la posición abierta"""
        try:
            if not self.posición_abierta:
                return False
            
            order = client.futures_create_order(
                symbol=SYMBOL,
                side='SELL',
                type='MARKET',
                quantity=self.entrada_cantidad
            )
            
            precio_cierre = float(order['avgPrice'])
            ganancia = (precio_cierre - self.entrada_precio) * self.entrada_cantidad
            ganancia_pct = (ganancia / (self.entrada_precio * self.entrada_cantidad)) * 100
            
            self.posición_abierta = False
            self.modelo.actualizar_win_rate(ganancia)
            
            self.historial.append({
                'timestamp': datetime.now(),
                'entrada': self.entrada_precio,
                'salida': precio_cierre,
                'ganancia': ganancia,
                'ganancia_pct': ganancia_pct,
                'razón': razón
            })
            
            emoji = "🟢" if ganancia > 0 else "🔴"
            print(f"\n{emoji} VENTA EJECUTADA - {razón}")
            print(f"   Entrada: ${self.entrada_precio:.2f}")
            print(f"   Salida: ${precio_cierre:.2f}")
            print(f"   Ganancia: ${ganancia:.2f} ({ganancia_pct:.2f}%)")
            print(f"   Win Rate: {self.modelo.win_rate*100:.1f}%")
            
            return True
        except Exception as e:
            print(f"❌ Error cerrando posición: {e}")
            return False
    
    def ejecutar_ciclo(self):
        """Ejecuta un ciclo de trading"""
        try:
            # 1. Obtener precio actual
            ticker = client.futures_symbol_ticker(symbol=SYMBOL)
            precio_actual = float(ticker['price'])
            
            # 2. Obtener datos
            df = obtener_datos_klines(SYMBOL, INTERVAL, LOOKBACK)
            if df is None:
                return
            
            df = calcular_features(df)
            
            # 3. Si hay posición abierta, verificar TP/SL
            if self.posición_abierta:
                if precio_actual >= self.tp_precio:
                    self.cerrar_posición("✅ TAKE PROFIT")
                elif precio_actual <= self.sl_precio:
                    self.cerrar_posición("❌ STOP LOSS")
            
            # 4. Re-entrenar si win rate cae o tiempo pasado
            tiempo_desde_reentrenamiento = time.time() - self.modelo.última_reentrenamiento
            if self.modelo.win_rate < 0.55 or tiempo_desde_reentrenamiento > 3600:  # 1 hora
                print("🔄 Re-entrenando modelo...")
                self.modelo.entrenar(df)
                self.modelo.última_reentrenamiento = time.time()
            
            # 5. Si no hay posición, buscar señal
            if not self.posición_abierta:
                predicción = self.modelo.predecir(df)
                
                if predicción and predicción['debería_comprar']:
                    print(f"\n📊 Señal: Confianza {predicción['confianza']*100:.1f}%")
                    self.abrir_posición(precio_actual)
            
            # 6. Log estado
            balance = self.obtener_balance()
            estado = "🟢 POSICIÓN ABIERTA" if self.posición_abierta else "⚫ EN ESPERA"
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {estado} | Precio: ${precio_actual:.2f} | Balance: ${balance:.2f} | Win Rate: {self.modelo.win_rate*100:.1f}%")
            
        except Exception as e:
            print(f"❌ Error en ciclo: {e}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("🤖 INTENTO 9 DINÁMICO - REPLIT")
    print("=" * 60)
    print(f"📍 Modo: {'TESTNET' if TESTNET else 'LIVE'}")
    print(f"📊 Símbolo: {SYMBOL}")
    print(f"⚙️  Leverage: {LEVERAGE}x")
    print(f"💰 Tamaño posición: {POSITION_SIZE} BTC")
    print("=" * 60)
    
    bot = TradingBot()
    
    if not bot.inicializar():
        print("❌ No se pudo inicializar el bot")
        return
    
    ciclo = 0
    while True:
        ciclo += 1
        print(f"\n▶️  Ciclo {ciclo}")
        bot.ejecutar_ciclo()
        
        # Espera 5 minutos antes del próximo ciclo
        time.sleep(300)

if __name__ == "__main__":
    main()
