# Smart-Thermostat-ESP32
DIY smart thermostat project for boilers with ESP32

# ESP32 Akıllı Termostat (MicroPython)

Bu proje, ESP32 ve DHT11 sensörü kullanarak ortam sıcaklığını ölçen ve hedeflenen sıcaklığa göre kombiyi (veya ısıtıcıyı) röle üzerinden otomatik olarak kontrol eden bir akıllı termostat sistemidir. Web arayüzü üzerinden kontrol edilebilir ve MicroPython ile yazılmıştır.

## Özellikler

- **Dinamik Web Arayüzü:** Ağdaki cihazlardan (PC, Telefon) IP adresi girilerek sıcaklık takibi ve hedef sıcaklık değişimi yapılabilir.
- **Histerezis (Tolerans) Koruması:** Sistem hedefe ulaştıktan sonra, sıcaklık hedef değerin 1 derece üstüne çıkana kadar kombiyi açık tutarak sürekli "aç-kapa" yapıp kombiyi yormasını engeller.
- **Watchdog (Bekçi Köpeği):** Olası Wi-Fi kopmaları veya kilitlenmelerde ESP32 kendini 30 saniye içinde otomatik resetler.
- **Hata Toleransı:** Sensör 3 kez üst üste hata verirse acil durum protokolü devreye girer ve kombiyi zorla kapatır.
- **Detaylı Loglama:** Sistemin açılış saatleri, röle tetiklemeleri, kullanıcı müdahaleleri ve hatalar tarih/saat damgası ile kaydedilir.

## Donanım Bağlantıları

| Bileşen | ESP32 Pini | Açıklama |
| :--- | :--- | :--- |
| **DHT11 Sensör** | `GPIO 4` | Veri pini. (Ayrıca VCC ve GND bağlanmalıdır) |
| **Röle Modülü** | `GPIO 5` | Sinyal pini. (Active Low çalışır. 0=Açık, 1=Kapalı) |

## Kurulum ve Kullanım

1. `main.py` dosyası içindeki şu kısımları kendi ağınıza göre düzenleyin:
   ```python
   ssid = 'WIFI_AG_ADINIZ'
   password = 'WIFI_SIFRENIZ'
