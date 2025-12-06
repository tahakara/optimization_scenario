import random
import csv
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# ----------------------------
# DÜZELTİLMİŞ TEK PARÇA KOD
# ----------------------------

# --- 1. Sabit Tanımlar ---
SUNUCU_SAYISI = 4
SIMULASYON_SURESI_SANIYE = 600
CPU_KAPASITE_LIMITI = 100.0   # Normalleştirilmiş CPU birimi (ör: 100 unit toplam)
time_step = 0.01              # Küçük time_step, performans maliyeti olabilir (opsiyonel büyütülebilir)

# Stabil ve Peak Yük Parametreleri (requests per minute)
STABIL_ISTEK_DAKIKA = 8000   # normal zamanlarda gelen istek sayısı (dakikada)
PEAK_ISTEK_DAKIKA = 25000    # peak saatlerde gelen istek sayısı (dakikada)

# Peak zamanları (saniye cinsinden)
PEAK_BASLANGIC_1 = 120  # 2. dakikada başlar
PEAK_BITIS_1 = 180      # 3. dakikada biter

PEAK_BASLANGIC_2 = 360  # 6. dakikada başlar
PEAK_BITIS_2 = 480      # 8. dakikada biter

# Ağırlıklar WRR için (sunucu başına)
AGIRLIKLAR = [5, 3, 2, 1]
# Sunucu işlem hızları (işlem süresini etkileyen factor)
ISLEM_HIZLARI = [1.0, 1.0, 1.0, 1.0]

# Request CPU ihtiyacı aralığı (aynı birimde - CPU unit)
# CPU_KAPASITE_LIMITI ile uyumlu aralık seçildi (ör: 5-20 unit)
REQ_CPU_MIN = 5.0
REQ_CPU_MAX = 20.0

OUTPUT_FOLDER = "simulasyon_grafikleri"
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

print(f"📊 Yük Bilgileri:")
print(f" Stabil: {STABIL_ISTEK_DAKIKA} req/dk (~{STABIL_ISTEK_DAKIKA/60:.1f} req/s)")
print(f" Peak: {PEAK_ISTEK_DAKIKA} req/dk (~{PEAK_ISTEK_DAKIKA/60:.1f} req/s)")
print(f" Peak Artışı: {PEAK_ISTEK_DAKIKA/STABIL_ISTEK_DAKIKA:.1f}x")
print(f"\n⚙️ Sunucu Yapılandırması:")
print(f" Ağırlıklar: {AGIRLIKLAR}")
print(f" İşlem Hızları: {ISLEM_HIZLARI}")
print(f" CPU Kapasite (unit): {CPU_KAPASITE_LIMITI}")
print(" NOT: CPU birimleri normalize edildi; Request CPU ihtiyacı REQ_CPU_MIN..MAX aralığında.\n")

def get_request_rate(current_time):
    """
    returns lambda = requests per second (float)
    -- DÜZELTME: orijinal kodda ters bölme vardı; burada doğru olarak requests/saniye veriyoruz.
    """
    if (PEAK_BASLANGIC_1 <= current_time < PEAK_BITIS_1) or \
       (PEAK_BASLANGIC_2 <= current_time < PEAK_BITIS_2):
        return PEAK_ISTEK_DAKIKA / 60.0
    else:
        return STABIL_ISTEK_DAKIKA / 60.0

# --- 2. Yardımcı Sınıflar ---
class Request:
    def __init__(self, id):
        self.id = id
        # CPU ihtiyacı aynı birimde (unit)
        self.cpu_ihtiyaci = random.uniform(REQ_CPU_MIN, REQ_CPU_MAX)
        # işlem süresi (saniye)
        self.islem_suresi = random.uniform(0.5, 3.0)
        self.gelis_zamani = 0.0
        # Kuyruğa giriş zamanını None olarak başlat (daha güvenli)
        self.kuyruga_giris_zamani = None
        self.tamamlanma_zamani = None

class Server:
    def __init__(self, id, islem_hizi=1.0):
        self.id = id
        self.kuyruk = []
        self.islenen_istekler = []
        self.mevcut_cpu_yuku = 0.0
        self.islem_hizi = islem_hizi
        self.islenen_istek_sayisi = 0
        self.toplam_bekleme_suresi = 0.0
        self.toplam_islem_suresi = 0.0
        self.aktif_request_sayisi = 0

# --- 3. Simülasyon Çekirdeği ---
def run_simulation(servers, algoritma_adi, wrr_agirliklari=None):
    """
    servers: list of Server objects (length SUNUCU_SAYISI)
    algoritma_adi: "RR", "WRR", "LC", "WLC"
    wrr_agirliklari: list of weights (aynı uzunlukta)
    """
    csv_filename = f"{algoritma_adi}_simulasyon_sonuclari.csv"
    
    with open(csv_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        header = ["Zaman (s)", "Toplam Kuyruk Uzunlugu", "Toplam Islenen Request"]
        for i in range(SUNUCU_SAYISI):
            header.append(f"S{i+1}_Kuyruk")
            header.append(f"S{i+1}_CPU")
        header.append("Ortalama_CPU_Kullanimi")
        header.append("Ortalama_Bekleme_Suresi")
        writer.writerow(header)

    current_time = 0.0
    request_id_counter = 0
    
    # İlk request rate'i dinamik olarak al
    current_rate = get_request_rate(current_time)
    # random.expovariate expects rate lambda (requests per second)
    next_arrival_time = current_time + random.expovariate(current_rate)
    
    # RR için index
    next_server_index = 0

    # WRR: deterministic wheel (kolay ve güvenilir)
    wrr_wheel = None
    wrr_pos = 0
    if algoritma_adi == "WRR" and wrr_agirliklari:
        wrr_wheel = []
        for i, w in enumerate(wrr_agirliklari):
            # weight sayısı çok büyükse normalize edilebilir; burada integer kabul ediyoruz
            times = max(1, int(w))
            wrr_wheel.extend([i] * times)
        # Eğer çark boşsa fallback
        if not wrr_wheel:
            wrr_wheel = list(range(SUNUCU_SAYISI))

    log_interval = 1.0
    next_log_time = 0.0
    
    # Simülasyon loop (time-step based)
    while True:
        # Döngü sonlandırma kontrolü
        if current_time >= SIMULASYON_SURESI_SANIYE:
            islem_devam_ediyor = any(s.kuyruk or s.islenen_istekler for s in servers)
            if not islem_devam_ediyor:
                break
        
        # --- İstek Gelişi ve Load Balancing ---
        # arrival(s) olabilir; tek tek ele alıyoruz
        if current_time >= next_arrival_time and current_time < SIMULASYON_SURESI_SANIYE:
            # Yeni istek oluştur
            request_id_counter += 1
            new_request = Request(request_id_counter)
            new_request.gelis_zamani = current_time

            server_index = -1
            
            if algoritma_adi == "RR":
                server_index = next_server_index % SUNUCU_SAYISI
                next_server_index += 1
                
            elif algoritma_adi == "WRR":
                # wheel'den al
                if wrr_wheel:
                    server_index = wrr_wheel[wrr_pos % len(wrr_wheel)]
                    wrr_pos += 1
                else:
                    server_index = next_server_index % SUNUCU_SAYISI
                    next_server_index += 1
                
            elif algoritma_adi == "LC":
                # least connections: kuyruk + işlenen
                min_connections = float('inf')
                for i, server in enumerate(servers):
                    total_connections = len(server.kuyruk) + len(server.islenen_istekler)
                    if total_connections < min_connections:
                        min_connections = total_connections
                        server_index = i
                
            elif algoritma_adi == "WLC":
                # weight'li least connections
                min_effective_load = float('inf')
                for i, server in enumerate(servers):
                    weight = (wrr_agirliklari[i] if wrr_agirliklari and i < len(wrr_agirliklari) else 1)
                    if weight == 0:
                        continue
                    total_connections = len(server.kuyruk) + len(server.islenen_istekler)
                    effective_load = total_connections / weight
                    if effective_load < min_effective_load:
                        min_effective_load = effective_load
                        server_index = i
            
            if server_index == -1:
                server_index = 0  # fallback
            
            target_server = servers[server_index]

            # Eğer seçilen sunucunun anlık CPU kapasitesi yetmiyorsa,
            # diğer sunucular arasında işleme alabilecek olanı bulmaya çalış.
            if target_server.mevcut_cpu_yuku + new_request.cpu_ihtiyaci > CPU_KAPASITE_LIMITI:
                alt_found = False
                for i, s in enumerate(servers):
                    if s.mevcut_cpu_yuku + new_request.cpu_ihtiyaci <= CPU_KAPASITE_LIMITI:
                        target_server = s
                        alt_found = True
                        break

                if not alt_found:
                    # Hiçbir sunucu anında işleyemiyorsa kuyrukla ekle
                    new_request.kuyruga_giris_zamani = current_time
                    target_server.kuyruk.append(new_request)
                    target_server.aktif_request_sayisi += 1
                    # sonraki geliş zamanını güncelle ve devam et
                    current_rate = get_request_rate(current_time)
                    interarrival = random.expovariate(current_rate)
                    next_arrival_time = current_time + interarrival
                    # bu time-step içinde diğer işler de yapılacak (yani don't continue)
            else:
                # CPU kapasitesi varsa hemen işle (target_server üzerinde)
                target_server.islenen_istekler.append(new_request)
                target_server.mevcut_cpu_yuku += new_request.cpu_ihtiyaci
                target_server.aktif_request_sayisi += 1

            # Her yeni gelişten sonra next_arrival_time'ı hesapla (current_time bazlı)
            current_rate = get_request_rate(current_time)
            interarrival = random.expovariate(current_rate)
            next_arrival_time = current_time + interarrival

        # --- Sunucu İşlemleri ---
        for server in servers:
            # İşlemdeki istekleri ilerlet
            for req in list(server.islenen_istekler):
                req.islem_suresi -= time_step * server.islem_hizi
                if req.islem_suresi <= 0:
                    # Tamamlandı
                    server.islenen_istekler.remove(req)
                    server.mevcut_cpu_yuku -= req.cpu_ihtiyaci
                    server.islenen_istek_sayisi += 1
                    server.aktif_request_sayisi = max(0, server.aktif_request_sayisi - 1)
                    req.tamamlanma_zamani = current_time
                    
                    # Bekleme süresini kaydet (sadece kuyruğa girenler için)
                    if req.kuyruga_giris_zamani is not None:
                        # İşlemeye başlama zamanı = tamamlama zamanı - işlem süresi işlenirken geçen süre
                        # Burada kuyruktan çıkış zamanı simülasyonda 'kuyruga_giris_zamani' ve
                        # işlem başlaması kaydedilmediği için, basitçe bekleme süresi:
                        server.toplam_bekleme_suresi += ( (req.tamamlanma_zamani - req.gelis_zamani) - (req.islem_suresi if req.islem_suresi>0 else 0) )
                        # Not: Bu ifade kaba bir tahmindir; detaylı bekleme zamanı için kuyruktan çıkış anını ayrı kaydetmek gerekir.
                    
                    server.toplam_islem_suresi += (req.tamamlanma_zamani - req.gelis_zamani)

            # Kuyruktan işleme geçiş (ilk uygun olan)
            if server.kuyruk:
                next_req = server.kuyruk[0]
                if server.mevcut_cpu_yuku + next_req.cpu_ihtiyaci <= CPU_KAPASITE_LIMITI:
                    server.kuyruk.pop(0)
                    # Başlangıçta kuyruğa giriş zamanı None değilse kalır
                    server.islenen_istekler.append(next_req)
                    server.mevcut_cpu_yuku += next_req.cpu_ihtiyaci
                    # aktif_request_sayisi değişmedi çünkü zaten sayılmıştı

        # --- CSV Kayıt ---
        if current_time >= next_log_time:
            log_data = [current_time]
            
            toplam_kuyruk = sum(len(s.kuyruk) for s in servers)
            toplam_islenen_kumulatif = sum(s.islenen_istek_sayisi for s in servers)
            log_data.extend([toplam_kuyruk, toplam_islenen_kumulatif])
            
            current_cpu_loads = []
            for server in servers:
                log_data.append(len(server.kuyruk))
                log_data.append(server.mevcut_cpu_yuku)
                current_cpu_loads.append(server.mevcut_cpu_yuku)
            
            ortalama_cpu = sum(current_cpu_loads) / SUNUCU_SAYISI if SUNUCU_SAYISI > 0 else 0.0
            log_data.append(ortalama_cpu)

            # Ortalama bekleme süresi (anlık) - toplam bekleme / işlenen
            toplam_bekleme_kumulatif = sum(s.toplam_bekleme_suresi for s in servers)
            ortalama_bekleme_anlik = toplam_bekleme_kumulatif / toplam_islenen_kumulatif if toplam_islenen_kumulatif > 0 else 0.0
            log_data.append(ortalama_bekleme_anlik)
            
            with open(csv_filename, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(log_data)
                
            next_log_time += log_interval
            
        current_time += time_step

    toplam_islenen = sum(s.islenen_istek_sayisi for s in servers)
    toplam_bekleme_suresi = sum(s.toplam_bekleme_suresi for s in servers)
    
    return toplam_islenen, toplam_bekleme_suresi, csv_filename, request_id_counter

# --- 4. Simülasyonları Çalıştır ---
print("🔄 Simülasyonlar başlatılıyor...")

servers_rr = [Server(i+1) for i in range(SUNUCU_SAYISI)]
rr_islenen, rr_bekleme, rr_csv, rr_gelen = run_simulation(servers_rr, "RR")

servers_wrr = [Server(i+1, ISLEM_HIZLARI[i]) for i in range(SUNUCU_SAYISI)]
wrr_islenen, wrr_bekleme, wrr_csv, wrr_gelen = run_simulation(servers_wrr, "WRR", AGIRLIKLAR[:SUNUCU_SAYISI])

servers_lc = [Server(i+1) for i in range(SUNUCU_SAYISI)]
lc_islenen, lc_bekleme, lc_csv, lc_gelen = run_simulation(servers_lc, "LC", [1]*SUNUCU_SAYISI)

servers_wlc = [Server(i+1, ISLEM_HIZLARI[i]) for i in range(SUNUCU_SAYISI)]
wlc_islenen, wlc_bekleme, wlc_csv, wlc_gelen = run_simulation(servers_wlc, "WLC", AGIRLIKLAR[:SUNUCU_SAYISI])

# --- 5. Sonuçlar ---
print("\n" + "="*50)
print("📊 SİMÜLASYON SONUÇLARI")
print("="*50)
print(f"Toplam Gelen İstek: {rr_gelen}")
print("-" * 50)

def print_results(alg_adi, islenen, bekleme, gelen):
    if islenen > 0:
        ortalama_bekleme = bekleme / islenen
        throughput = islenen / SIMULASYON_SURESI_SANIYE
        kayip_oran = ((gelen - islenen) / gelen * 100) if gelen > 0 else 0
        print(f"{alg_adi:4} | İşlenen: {islenen:6} | Kayıp: %{kayip_oran:5.2f} | Ort.Bekleme: {ortalama_bekleme:7.4f}s | Throughput: {throughput:6.2f} req/s")
    else:
        print(f"{alg_adi:4} | İşlenen: {islenen:6} | YETERSİZ TRAFİK")

print_results("RR", rr_islenen, rr_bekleme, rr_gelen)
print_results("WRR", wrr_islenen, wrr_bekleme, wrr_gelen)
print_results("LC", lc_islenen, lc_bekleme, lc_gelen)
print_results("WLC", wlc_islenen, wlc_bekleme, wlc_gelen)
print("="*50)

# --- 6. Görselleştirme ---
def visualize_all_results(csv_files, sim_suresi):
    df = {alg: pd.read_csv(f) for alg, f in csv_files.items()}
    plt.style.use('ggplot')
    
    def add_peak_zones(ax):
        ax.axvspan(PEAK_BASLANGIC_1, PEAK_BITIS_1, alpha=0.15, color='red', label='Peak Dönem', zorder=0)
        ax.axvspan(PEAK_BASLANGIC_2, PEAK_BITIS_2, alpha=0.15, color='red', zorder=0)
    
    # Grafik 1: Kuyruk Uzunluğu
    plt.figure(figsize=(12, 6))
    for alg, d in df.items():
        plt.plot(d['Zaman (s)'], d['Toplam Kuyruk Uzunlugu'], label=alg, alpha=0.8, linewidth=2)
    add_peak_zones(plt.gca())
    plt.title('Zamana Göre Toplam Kuyruk Uzunluğu', fontsize=14, fontweight='bold')
    plt.xlabel('Zaman (saniye)')
    plt.ylabel('Kuyrukta Bekleyen İstek Sayısı')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FOLDER, 'kuyruk_uzunlugu.png'), dpi=150)
    plt.close()

    # Grafik 2: İşlenen Request
    plt.figure(figsize=(12, 6))
    for alg, d in df.items():
        plt.plot(d['Zaman (s)'], d['Toplam Islenen Request'], label=alg, alpha=0.8, linewidth=2)
    add_peak_zones(plt.gca())
    plt.title('Kümülatif İşlenen İstek Sayısı', fontsize=14, fontweight='bold')
    plt.xlabel('Zaman (saniye)')
    plt.ylabel('Toplam İşlenen İstek')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FOLDER, 'islenen_request.png'), dpi=150)
    plt.close()

    # Grafik 3: RR vs WRR CPU
    plt.figure(figsize=(12, 6))
    plt.plot(df["RR"]['Zaman (s)'], df["RR"]['Ortalama_CPU_Kullanimi'], label='RR', linewidth=2)
    plt.plot(df["WRR"]['Zaman (s)'], df["WRR"]['Ortalama_CPU_Kullanimi'], label='WRR', linewidth=2)
    add_peak_zones(plt.gca())
    plt.title('RR vs WRR: Ortalama CPU Kullanımı (unit)', fontsize=14, fontweight='bold')
    plt.xlabel('Zaman (saniye)')
    plt.ylabel('CPU Kullanımı (unit)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FOLDER, 'rr_wrr_cpu.png'), dpi=150)
    plt.close()

    # Grafik 4: LC vs WLC CPU
    plt.figure(figsize=(12, 6))
    plt.plot(df["LC"]['Zaman (s)'], df["LC"]['Ortalama_CPU_Kullanimi'], label='LC', linewidth=2)
    plt.plot(df["WLC"]['Zaman (s)'], df["WLC"]['Ortalama_CPU_Kullanimi'], label='WLC', linewidth=2)
    add_peak_zones(plt.gca())
    plt.title('LC vs WLC: Ortalama CPU Kullanımı (unit)', fontsize=14, fontweight='bold')
    plt.xlabel('Zaman (saniye)')
    plt.ylabel('CPU Kullanımı (unit)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FOLDER, 'lc_wlc_cpu.png'), dpi=150)
    plt.close()

    # Ortalama Bekleme Süresi (zaman serisi)
    plt.figure(figsize=(12, 6))
    for alg, d in df.items():
        plt.plot(d['Zaman (s)'], d['Ortalama_Bekleme_Suresi'], label=alg, alpha=0.8, linewidth=2)
    add_peak_zones(plt.gca())
    plt.title('Zamana Göre Ortalama Kuyrukta Bekleme Süresi', fontsize=14, fontweight='bold')
    plt.xlabel('Zaman (saniye)')
    plt.ylabel('Ortalama Bekleme Süresi (saniye)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FOLDER, 'ortalama_bekleme_suresi.png'), dpi=150)
    plt.close()

    # Sunucu bazlı CPU grafikleri
    algorithms = ["RR", "WRR", "LC", "WLC"]
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    for alg in algorithms:
        plt.figure(figsize=(14, 7))
        for i in range(SUNUCU_SAYISI):
            cpu_column = f'S{i+1}_CPU'
            plt.plot(df[alg]['Zaman (s)'], df[alg][cpu_column], label=f'Sunucu {i+1}', linewidth=2, alpha=0.8)
        add_peak_zones(plt.gca())
        plt.axhline(y=CPU_KAPASITE_LIMITI, color='red', linestyle=':', label=f'CPU Limit ({CPU_KAPASITE_LIMITI})', alpha=0.7)
        plt.title(f'{alg} - Sunucu Bazlı CPU Kullanımı (unit)', fontsize=14, fontweight='bold')
        plt.xlabel('Zaman (saniye)')
        plt.ylabel('CPU (unit)')
        plt.legend(loc='best')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_FOLDER, f'{alg}_sunucu_cpu.png'), dpi=150)
        plt.close()

    # Throughput (işlenen/saniye)
    plt.figure(figsize=(12, 6))
    for alg, d in df.items():
        throughput = d['Toplam Islenen Request'].diff().fillna(0)
        throughput_smooth = throughput.rolling(window=10, center=True).mean()
        plt.plot(d['Zaman (s)'], throughput_smooth, label=alg, alpha=0.8, linewidth=2)
    add_peak_zones(plt.gca())
    plt.title('Request İşleme Hızı (Throughput)', fontsize=14, fontweight='bold')
    plt.xlabel('Zaman (saniye)')
    plt.ylabel('İşlenen Request / Saniye')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FOLDER, 'throughput.png'), dpi=150)
    plt.close()

csv_files = {"RR": rr_csv, "WRR": wrr_csv, "LC": lc_csv, "WLC": wlc_csv}
visualize_all_results(csv_files, SIMULASYON_SURESI_SANIYE)

print(f"\n✅ Grafikler '{OUTPUT_FOLDER}' klasörüne kaydedildi.")
