import machine
import dht
import network
import socket
import time
import ntptime
import gc

# --- DONANIM VE BEKÇİ KÖPEĞİ (WATCHDOG) ---
wdt = machine.WDT(timeout=30000) 
dht_pin = machine.Pin(4)
sensor = dht.DHT11(dht_pin)

role_pin = machine.Pin(5, machine.Pin.OPEN_DRAIN)
role_pin.value(1) # Başlangıç: KAPALI

# --- DEĞİŞKENLER VE HAFIZA ---
AYAR_DOSYASI = 'ayarlar.txt'
LOG_DOSYASI = 'log.txt'

sensor_hata_sayaci = 0
eski_role_durumu = 1 
son_olcum = 0 
anlik_sicaklik = "Bekleniyor..."
anlik_nem = "Bekleniyor..."

def ayarlari_oku():
    try:
        with open(AYAR_DOSYASI, 'r') as f:
            veri = f.read().split(',')
            return float(veri[0]), True if int(veri[1]) == 1 else False
    except:
        return 23.0, True

def ayarlari_kaydet(hedef, sistem_durumu):
    try:
        with open(AYAR_DOSYASI, 'w') as f:
            f.write(f"{hedef},{1 if sistem_durumu else 0}")
    except:
        pass

hedef_sicaklik, sistem_acik = ayarlari_oku()

# --- ZAMAN VE LOG SİSTEMİ ---
def saati_guncelle():
    for _ in range(5):
        try:
            ntptime.settime()
            return True
        except:
            time.sleep(2)
            wdt.feed() 
    return False

def turkiye_saati():
    t = time.localtime(time.time() + 10800)
    return f"{t[0]}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}:{t[5]:02d}"

def log_yaz(mesaj):
    zaman = turkiye_saati()
    satir = f"[{zaman}] {mesaj}\n"
    print(satir, end="")
    try:
        with open(LOG_DOSYASI, 'a') as f:
            f.write(satir)
    except:
        pass

def log_oku():
    try:
        with open(LOG_DOSYASI, 'r') as f:
            return f.read()
    except:
        return "Henüz bir kayıt yok veya dosya okunamadı."

# --- WIFI VE SABİT IP ---
# LÜTFEN KENDİ WIFI BİLGİLERİNİZİ GİRİN
ssid = 'WIFI_AG_ADINIZ'
password = 'WIFI_SIFRENIZ'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
# Sabit IP ayarı: IP, Alt Ağ Maskesi, Ağ Geçidi, DNS
wlan.ifconfig(('192.168.1.150', '255.255.255.0', '192.168.1.1', '8.8.8.8'))
wlan.connect(ssid, password)

print("WiFi Bekleniyor...")
while not wlan.isconnected():
    wdt.feed() 
    time.sleep(1)

if saati_guncelle():
    log_yaz("SISTEM BASLATILDI. Saat basariyla alindi. IP: 192.168.1.150")
else:
    log_yaz("SISTEM BASLATILDI. Saat ALINAMADI!")

# --- WEB ARAYÜZÜ ---
def ana_sayfa(sicaklik, nem, role_durumu, hedef, sistem_aktif_mi):
    kombi_metni = "ÇALIŞIYOR" if role_durumu == 0 else "BEKLEMEDE"
    kombi_renk = "#4CAF50" if role_durumu == 0 else "#f44336"
    sistem_metni = "SİSTEM AKTİF" if sistem_aktif_mi else "SİSTEM KAPALI"
    sistem_renk = "#2196F3" if sistem_aktif_mi else "#757575"
    
    html = f"""<!DOCTYPE html>
    <html>
    <head><title>Akilli Termostat</title><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="5">
    <style>
        body {{ font-family: Arial; text-align: center; background: #121212; color: white; margin-top: 30px; }}
        .kutu {{ background: #1e1e1e; padding: 20px; border-radius: 10px; display: inline-block; border-top: 5px solid {kombi_renk}; width: 85%; max-width: 400px; }}
        .btn {{ display: inline-block; padding: 15px; font-size: 20px; color: white; text-decoration: none; border-radius: 8px; margin: 5px; border: none; }}
    </style></head>
    <body>
        <h2 style="color:{sistem_renk}">{sistem_metni}</h2>
        <div class="kutu">
            <p>Ortam: <strong>{sicaklik}°C</strong> | Nem: <strong>%{nem}</strong></p><hr>
            <p>Durum: <strong style="color:{kombi_renk}">{kombi_metni}</strong></p>
            <h3 style="color:#ff9800">Hedef: {hedef}°C</h3>
            <a href="/?hedef=arttir" class="btn" style="background:#ff9800; width:35%;">+ Artır</a>
            <a href="/?hedef=azalt" class="btn" style="background:#ffb74d; color:#000; width:35%;">- Azalt</a>
        </div><br>
        <a href="/?sistem={'kapat' if sistem_aktif_mi else 'ac'}" class="btn" style="background:{'#f44336' if sistem_aktif_mi else '#4CAF50'}; width:85%; max-width:400px; margin-top:20px;">
            Sistemi {'Kapat' if sistem_aktif_mi else 'Aç (Oto)'}
        </a><br><br>
        <a href="/log" style="color:#888;">Sistem Kayıtlarını (Log) Gör</a>
    </body></html>"""
    return html

# --- SUNUCU BAŞLATMA ---
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 80))
s.listen(5)

while True:
    wdt.feed() 
    
    if not wlan.isconnected():
        try:
            wlan.connect(ssid, password)
        except:
            pass

    # 1. ADIM: SENSÖR VE RÖLE KONTROLÜ
    if time.ticks_diff(time.ticks_ms(), son_olcum) > 2000:
        try:
            sensor.measure()
            anlik_sicaklik = sensor.temperature()
            anlik_nem = sensor.humidity()
            sensor_hata_sayaci = 0 
            
            if not sistem_acik:
                role_pin.value(1) 
            else:
                if anlik_sicaklik < hedef_sicaklik:
                    role_pin.value(0)
                elif anlik_sicaklik >= (hedef_sicaklik + 1.0):
                    role_pin.value(1)
                    
        except OSError:
            sensor_hata_sayaci += 1
            if sensor_hata_sayaci >= 3: 
                anlik_sicaklik = "Hata"
                anlik_nem = "Hata"
                role_pin.value(1)
                if sensor_hata_sayaci == 3: 
                    log_yaz("DIKKAT: Sensor okuma hatasi! Kombi kapatildi.")
            
        yeni_role_durumu = role_pin.value()
        if yeni_role_durumu != eski_role_durumu:
            durum_mesaj = "ACILDI" if yeni_role_durumu == 0 else "KAPATILDI"
            log_yaz(f"ROLE TETIKLENDI: Kombi {durum_mesaj}.")
            eski_role_durumu = yeni_role_durumu
            
        son_olcum = time.ticks_ms()

    # 2. ADIM: WEB SUNUCUSU
    try:
        s.settimeout(0.5) 
        conn, addr = s.accept()
        
        try: 
            conn.settimeout(1.0)
            request = conn.recv(1024).decode('utf-8')
            yonlendir = False
            
            if '/?hedef=arttir' in request:
                hedef_sicaklik += 1.0
                ayarlari_kaydet(hedef_sicaklik, sistem_acik)
                log_yaz(f"KULLANICI: Hedef sicaklik artirildi -> {hedef_sicaklik}C")
                yonlendir = True
            elif '/?hedef=azalt' in request:
                hedef_sicaklik -= 1.0
                ayarlari_kaydet(hedef_sicaklik, sistem_acik)
                log_yaz(f"KULLANICI: Hedef sicaklik azaltildi -> {hedef_sicaklik}C")
                yonlendir = True
            elif '/?sistem=ac' in request:
                sistem_acik = True
                ayarlari_kaydet(hedef_sicaklik, sistem_acik)
                log_yaz("KULLANICI: Sistem ANA SALTERDEN ACILDI.")
                yonlendir = True
            elif '/?sistem=kapat' in request:
                sistem_acik = False
                ayarlari_kaydet(hedef_sicaklik, sistem_acik)
                log_yaz("KULLANICI: Sistem ANA SALTERDEN KAPATILDI.")
                yonlendir = True
                
            if yonlendir:
                conn.send('HTTP/1.1 303 See Other\nLocation: /\nConnection: close\n\n')
            elif '/log' in request:
                log_verisi = log_oku()
                conn.send('HTTP/1.1 200 OK\nContent-Type: text/plain\nConnection: close\n\n')
                conn.sendall(log_verisi)
            else:
                response = ana_sayfa(anlik_sicaklik, anlik_nem, role_pin.value(), hedef_sicaklik, sistem_acik)
                conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\nConnection: close\n\n')
                conn.sendall(response)
        except OSError:
            pass 
        finally:
            conn.close() 
            gc.collect() 
            
    except OSError:
        pass
