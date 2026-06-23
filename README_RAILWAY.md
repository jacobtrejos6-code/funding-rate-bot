# 🚀 FUNDING RATE BOT - RAILWAY DEPLOYMENT

## ¿Qué es esto?

Tu Funding Rate Bot (que ganaba $0.15/día) ahora corre en la nube.
**No necesitas PC encendida.** Railway lo mantiene corriendo 24/7.

---

## 📋 REQUISITOS

1. Cuenta en Railway.app (gratis)
2. Proyecto en GitHub (o ZIP)
3. API Key + Secret de Binance

---

## ⚡ PASOS PARA DEPLOYAR

### PASO 1: Descarga estos 3 archivos

```
1. funding_rate_railway.py
2. requirements.txt
3. Procfile
```

### PASO 2: Crea carpeta en tu PC

```
C:\Users\hp\Funding_Bot_Railway\
```

Pon los 3 archivos ahí.

### PASO 3: Crea repositorio en GitHub

1. Ve a https://github.com/new
2. Crea repo: **funding-rate-bot**
3. Copia los comandos que te da GitHub

### PASO 4: Sube archivos a GitHub

En PowerShell (en tu carpeta):

```powershell
git init
git add .
git commit -m "Funding Rate Bot para Railway"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/funding-rate-bot.git
git push -u origin main
```

### PASO 5: Deployar a Railway

1. Ve a https://railway.app
2. Login con GitHub
3. Click **New Project** → **Deploy from GitHub**
4. Selecciona tu repo **funding-rate-bot**
5. Railway detectará `Procfile` automáticamente
6. Click **Deploy**

### PASO 6: Agregar Variables de Entorno

En Railway, ve a **Settings** → **Variables**

Agrega:

```
BINANCE_API_KEY = tu_api_key_aqui
BINANCE_API_SECRET = tu_api_secret_aqui
```

### PASO 7: ¡Listo!

El bot corre en la nube 24/7.

---

## 📊 VERIFICAR QUE FUNCIONA

1. En Railway, abre **Deployments**
2. Deberías ver logs como:

```
🟢 FUNDING RATE BOT - BTC/USDT (RAILWAY VERSION)
💵 Capital: $50
⚡ Leverage: 5x

🔄 CICLO 1 | 2026-06-23 15:30:00
📊 Funding Rate: 0.0025%
💰 Balance: $146.13 USDT
```

---

## 💰 COSTO

- **Primer mes**: GRATIS (saldo inicial Railway)
- **Después**: ~$5-10/mes (lo gana el bot en 1-2 meses)
- **Si saldo se acaba**: Vuelves a ejecutar en tu PC (sin railway)

---

## 🛠️ TROUBLESHOOTING

**Error: "BINANCE_API_KEY no encontrado"**
→ Agregaste las variables en Railway Settings?

**Error: "Módulo ccxt no encontrado"**
→ Railway instala `requirements.txt` automáticamente (espera 2 min)

**Bot no gana nada**
→ Normal, funding rate suele ser 0% (espera 8 horas)

---

## ✅ LISTO

Bot corriendo 24/7 sin tu PC. 

Ganancias automáticas: +$0.15/día

¿Preguntas? Pregunta en el chat.
