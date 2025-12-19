import random
import csv
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os


# --- 1. Sabit Tanımlar ---
SUNUCU_SAYISI = 4
SIMULASYON_SURESI_SANIYE = 600
CPU_KAPASITE_LIMITI = 100.0   # Normalleştirilmiş CPU birimi (ör: 100 unit toplam)
time_step = 0.01              # Küçük time_step, performans maliyeti olabilir (opsiyonel büyütülebilir)

# Stabil ve Peak Yük Parametreleri (requests per minute)
STABIL_ISTEK_DAKIKA = 8000   # normal zamanlarda gelen istek sayısı (dakikada)
PEAK_ISTEK_DAKIKA = 20000    # peak saatlerde gelen istek sayısı (dakikada) - TEST İÇİN DÜŞÜRÜLDÜ

# Peak zamanları (saniye cinsinden)
PEAK_BASLANGIC_1 = 120  # 2. dakikada başlar
PEAK_BITIS_1 = 180      # 3. dakikada biter

PEAK_BASLANGIC_2 = 360  # 6. dakikada başlar
PEAK_BITIS_2 = 480      # 8. dakikada biter

# Ağırlıklar WRR için (sunucu başına)
AGIRLIKLAR = [5, 3, 2, 1]
# Sunucu işlem hızları (işlem süresini etkileyen factor)
# Ağırlıklarla orantılı: yüksek ağırlık = daha hızlı işlem
ISLEM_HIZLARI = [1.5, 1.2, 1.0, 0.8]

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
    def __init__(self, id, gelis_zamani=0.0):
        self.id = id
        # CPU ihtiyacı aynı birimde (unit)
        self.cpu_ihtiyaci = random.uniform(REQ_CPU_MIN, REQ_CPU_MAX)
        # işlem süresi (saniye) - orijinal süreyi sakla
        self.orijinal_islem_suresi = random.uniform(0.5, 3.0)
        self.islem_suresi = self.orijinal_islem_suresi
        self.gelis_zamani = gelis_zamani
        # Kuyruğa giriş zamanını None olarak başlat (daha güvenli)
        self.kuyruga_giris_zamani = None
        self.isleme_baslama_zamani = None
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

# --- 3. İstek Serisini Önceden Oluştur ---
def generate_request_sequence(seed=None):
    """
    Tüm simülasyonlar için aynı istek serisini oluştur
    seed=None ise tamamen rastgele, aksi halde sabit seed kullanır
    """
    if seed is not None:
        random.seed(seed)
    
    requests = []
    current_time = 0.0
    request_id = 0
    
    current_rate = get_request_rate(current_time)
    next_arrival_time = current_time + random.expovariate(current_rate)
    
    while next_arrival_time < SIMULASYON_SURESI_SANIYE:
        request_id += 1
        req = Request(request_id, next_arrival_time)
        requests.append(req)
        
        current_rate = get_request_rate(next_arrival_time)
        interarrival = random.expovariate(current_rate)
        next_arrival_time = next_arrival_time + interarrival
    
    seed_msg = f"seed={seed}" if seed is not None else "rastgele"
    print(f"✅ {len(requests)} istek önceden oluşturuldu ({seed_msg})")
    return requests

# --- 4. Simülasyon Çekirdeği ---
def run_simulation(servers, algoritma_adi, request_sequence, wrr_agirliklari=None):
    """
    servers: list of Server objects (length SUNUCU_SAYISI)
    algoritma_adi: "RR", "WRR", "LC", "WLC"
    request_sequence: önceden oluşturulmuş istek listesi
    wrr_agirliklari: list of weights (aynı uzunlukta)
    """
    csv_filename = f"{algoritma_adi.lower()}_simulation_results.csv"
    
    with open(csv_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        header = ["time_seconds", "total_queue_length", "total_processed_requests"]
        for i in range(SUNUCU_SAYISI):
            header.append(f"server_{i+1}_queue")
            header.append(f"server_{i+1}_cpu")
        header.append("average_cpu_usage")
        header.append("average_wait_time")
        writer.writerow(header)

    current_time = 0.0
    
    # İstek sırasını kopyala (her Request nesnesini yeniden klonla)
    pending_requests = []
    for orig_req in request_sequence:
        new_req = Request(orig_req.id, orig_req.gelis_zamani)
        new_req.cpu_ihtiyaci = orig_req.cpu_ihtiyaci
        new_req.orijinal_islem_suresi = orig_req.orijinal_islem_suresi
        new_req.islem_suresi = orig_req.orijinal_islem_suresi
        pending_requests.append(new_req)
    
    request_index = 0
    next_arrival_time = pending_requests[0].gelis_zamani if pending_requests else float('inf')
    
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
        if current_time >= next_arrival_time and request_index < len(pending_requests):
            # Sıradaki isteği al
            new_request = pending_requests[request_index]
            request_index += 1

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
                
            # --- Güncellenmiş WLC Algoritması ---
            # CPU yüküne verilen ağırlık azaltıldı ve dinamik ağırlıklandırma eklendi.
            elif algoritma_adi == "WLC":
                # weight'li least connections
                min_effective_load = float('inf')
                for i, server in enumerate(servers):
                    weight = (wrr_agirliklari[i] if wrr_agirliklari and i < len(wrr_agirliklari) else 1)
                    if weight == 0:
                        continue
                    # Toplam aktif request sayısı (kuyruk + işlenen)
                    total_connections = len(server.kuyruk) + len(server.islenen_istekler)
                    # CPU kullanım oranı
                    cpu_usage_ratio = server.mevcut_cpu_yuku / CPU_KAPASITE_LIMITI
                    # Sunucunun kapasitesini göz önünde bulundur
                    capacity = weight * server.islem_hizi
                    # Hem connection hem CPU yükü (CPU ağırlığı azaltıldı)
                    effective_load = (total_connections / capacity + cpu_usage_ratio * 5) if capacity > 0 else float('inf')
                    if effective_load < min_effective_load:
                        min_effective_load = effective_load
                        server_index = i

                # Dinamik ağırlıklandırma
                for i, server in enumerate(servers):
                    wrr_agirliklari[i] = max(1, CPU_KAPASITE_LIMITI - server.mevcut_cpu_yuku)

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
            else:
                # CPU kapasitesi varsa hemen işle (target_server üzerinde)
                new_request.isleme_baslama_zamani = current_time
                target_server.islenen_istekler.append(new_request)
                target_server.mevcut_cpu_yuku += new_request.cpu_ihtiyaci
                target_server.aktif_request_sayisi += 1

            # Sonraki isteğin geliş zamanını ayarla
            if request_index < len(pending_requests):
                next_arrival_time = pending_requests[request_index].gelis_zamani
            else:
                next_arrival_time = float('inf')

        # --- Sunucu İşlemleri ---
        for server in servers:
            # İşlemdeki istekleri ilerlet
            for req in list(server.islenen_istekler):
                req.islem_suresi -= time_step * server.islem_hizi
                if req.islem_suresi <= 0:
                    # Tamamlandı
                    server.islenen_istekler.remove(req)
                    server.mevcut_cpu_yuku = max(0, server.mevcut_cpu_yuku - req.cpu_ihtiyaci)
                    server.islenen_istek_sayisi += 1
                    server.aktif_request_sayisi = max(0, server.aktif_request_sayisi - 1)
                    req.tamamlanma_zamani = current_time
                    
                    # Bekleme süresini kaydet (sadece kuyruğa girenler için)
                    if req.kuyruga_giris_zamani is not None and req.isleme_baslama_zamani is not None:
                        # Gerçek kuyrukta bekleme süresi
                        bekleme_suresi = req.isleme_baslama_zamani - req.kuyruga_giris_zamani
                        server.toplam_bekleme_suresi += max(0, bekleme_suresi)
                    
                    # Toplam işlem süresi (sistemde kalma süresi)
                    server.toplam_islem_suresi += (req.tamamlanma_zamani - req.gelis_zamani)

            # Kuyruktan işleme geçiş (ilk uygun olan)
            if server.kuyruk:
                next_req = server.kuyruk[0]
                if server.mevcut_cpu_yuku + next_req.cpu_ihtiyaci <= CPU_KAPASITE_LIMITI:
                    server.kuyruk.pop(0)
                    # İşleme başlama zamanını kaydet
                    next_req.isleme_baslama_zamani = current_time
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
    
    return toplam_islenen, toplam_bekleme_suresi, csv_filename

# --- 5. Simülasyonları Çalıştır ---
print("🔄 Simülasyonlar başlatılıyor...")

# Tüm algoritmalar için aynı istek serisini oluştur
# seed=None: Tamamen rastgele yük dağılımı
# seed=42: Tekrarlanabilir sonuçlar için sabit seed
request_sequence = generate_request_sequence(seed=None)
total_requests = len(request_sequence)

servers_rr = [Server(i+1) for i in range(SUNUCU_SAYISI)]
rr_islenen, rr_bekleme, rr_csv = run_simulation(servers_rr, "RR", request_sequence)

servers_wrr = [Server(i+1, ISLEM_HIZLARI[i]) for i in range(SUNUCU_SAYISI)]
wrr_islenen, wrr_bekleme, wrr_csv = run_simulation(servers_wrr, "WRR", request_sequence, AGIRLIKLAR[:SUNUCU_SAYISI])

servers_lc = [Server(i+1) for i in range(SUNUCU_SAYISI)]
lc_islenen, lc_bekleme, lc_csv = run_simulation(servers_lc, "LC", request_sequence, [1]*SUNUCU_SAYISI)

servers_wlc = [Server(i+1, ISLEM_HIZLARI[i]) for i in range(SUNUCU_SAYISI)]
wlc_islenen, wlc_bekleme, wlc_csv = run_simulation(servers_wlc, "WLC", request_sequence, AGIRLIKLAR[:SUNUCU_SAYISI])

# --- 6. Sonuçlar ---
print("\n" + "="*50)
print("📊 SİMÜLASYON SONUÇLARI")
print("="*50)
print(f"Toplam Gelen İstek: {total_requests}")
print("-" * 50)

# --- Yeni Metrikler ---
# Ortalama kuyruk uzunluğu ve sunucu başına işlenen istek sayısı eklendi.
def print_results(alg_adi, islenen, bekleme, gelen, servers):
    if islenen > 0:
        ortalama_bekleme = bekleme / islenen
        throughput = islenen / SIMULASYON_SURESI_SANIYE
        kayip_oran = ((gelen - islenen) / gelen * 100) if gelen > 0 else 0
        ortalama_kuyruk = sum(len(s.kuyruk) for s in servers) / len(servers)
        print(f"{alg_adi:4} | İşlenen: {islenen:6} | Kayıp: %{kayip_oran:5.2f} | Ort.Bekleme: {ortalama_bekleme:7.4f}s | Throughput: {throughput:6.2f} req/s | Ort.Kuyruk: {ortalama_kuyruk:.2f}")
        for i, server in enumerate(servers):
            print(f"  Sunucu {i+1}: İşlenen İstek: {server.islenen_istek_sayisi}")
    else:
        print(f"{alg_adi:4} | İşlenen: {islenen:6} | YETERSİZ TRAFİK")

print_results("RR", rr_islenen, rr_bekleme, total_requests, servers_rr)
print_results("WRR", wrr_islenen, wrr_bekleme, total_requests, servers_wrr)
print_results("LC", lc_islenen, lc_bekleme, total_requests, servers_lc)
print_results("WLC", wlc_islenen, wlc_bekleme, total_requests, servers_wlc)
print("="*50)

# --- 7. Görselleştirme ---
def visualize_all_results(csv_files, sim_suresi):
    df = {alg: pd.read_csv(f) for alg, f in csv_files.items()}
    plt.style.use('ggplot')
    
    def add_peak_zones(ax):
        ax.axvspan(PEAK_BASLANGIC_1, PEAK_BITIS_1, alpha=0.15, color='red', label='Peak Dönem', zorder=0)
        ax.axvspan(PEAK_BASLANGIC_2, PEAK_BITIS_2, alpha=0.15, color='red', zorder=0)
    
    # Grafik 1: Kuyruk Uzunluğu
    plt.figure(figsize=(12, 6))
    for alg, d in df.items():
        plt.plot(d['time_seconds'], d['total_queue_length'], label=alg, alpha=0.8, linewidth=2)
    add_peak_zones(plt.gca())
    plt.title('Zamana Göre Toplam Kuyruk Uzunluğu', fontsize=14, fontweight='bold')
    plt.xlabel('Zaman (saniye)')
    plt.ylabel('Kuyrukta Bekleyen İstek Sayısı')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FOLDER, 'queue_length.png'), dpi=150)
    plt.close()

    # Grafik 2: İşlenen Request
    plt.figure(figsize=(12, 6))
    for alg, d in df.items():
        plt.plot(d['time_seconds'], d['total_processed_requests'], label=alg, alpha=0.8, linewidth=2)
    add_peak_zones(plt.gca())
    plt.title('Kümülatif İşlenen İstek Sayısı', fontsize=14, fontweight='bold')
    plt.xlabel('Zaman (saniye)')
    plt.ylabel('Toplam İşlenen İstek')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FOLDER, 'processed_requests.png'), dpi=150)
    plt.close()

    # Grafik 3: RR vs WRR CPU
    plt.figure(figsize=(12, 6))
    plt.plot(df["RR"]['time_seconds'], df["RR"]['average_cpu_usage'], label='RR', linewidth=2)
    plt.plot(df["WRR"]['time_seconds'], df["WRR"]['average_cpu_usage'], label='WRR', linewidth=2)
    add_peak_zones(plt.gca())
    plt.title('RR vs WRR: Ortalama CPU Kullanımı (unit)', fontsize=14, fontweight='bold')
    plt.xlabel('Zaman (saniye)')
    plt.ylabel('CPU Kullanımı (unit)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FOLDER, 'rr_vs_wrr_cpu.png'), dpi=150)
    plt.close()

    # Grafik 4: LC vs WLC CPU
    plt.figure(figsize=(12, 6))
    plt.plot(df["LC"]['time_seconds'], df["LC"]['average_cpu_usage'], label='LC', linewidth=2)
    plt.plot(df["WLC"]['time_seconds'], df["WLC"]['average_cpu_usage'], label='WLC', linewidth=2)
    add_peak_zones(plt.gca())
    plt.title('LC vs WLC: Ortalama CPU Kullanımı (unit)', fontsize=14, fontweight='bold')
    plt.xlabel('Zaman (saniye)')
    plt.ylabel('CPU Kullanımı (unit)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FOLDER, 'lc_vs_wlc_cpu.png'), dpi=150)
    plt.close()

    # Ortalama Bekleme Süresi (zaman serisi)
    plt.figure(figsize=(12, 6))
    for alg, d in df.items():
        plt.plot(d['time_seconds'], d['average_wait_time'], label=alg, alpha=0.8, linewidth=2)
    add_peak_zones(plt.gca())
    plt.title('Zamana Göre Ortalama Kuyrukta Bekleme Süresi', fontsize=14, fontweight='bold')
    plt.xlabel('Zaman (saniye)')
    plt.ylabel('Ortalama Bekleme Süresi (saniye)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FOLDER, 'average_wait_time.png'), dpi=150)
    plt.close()

    # Sunucu bazlı CPU grafikleri
    algorithms = ["RR", "WRR", "LC", "WLC"]
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    for alg in algorithms:
        plt.figure(figsize=(14, 7))
        for i in range(SUNUCU_SAYISI):
            cpu_column = f'server_{i+1}_cpu'
            plt.plot(df[alg]['time_seconds'], df[alg][cpu_column], label=f'Sunucu {i+1}', linewidth=2, alpha=0.8)
        add_peak_zones(plt.gca())
        plt.axhline(y=CPU_KAPASITE_LIMITI, color='red', linestyle=':', label=f'CPU Limit ({CPU_KAPASITE_LIMITI})', alpha=0.7)
        plt.title(f'{alg} - Sunucu Bazlı CPU Kullanımı (unit)', fontsize=14, fontweight='bold')
        plt.xlabel('Zaman (saniye)')
        plt.ylabel('CPU (unit)')
        plt.legend(loc='best')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_FOLDER, f'{alg.lower()}_server_cpu.png'), dpi=150)
        plt.close()

    # Throughput (işlenen/saniye)
    plt.figure(figsize=(12, 6))
    for alg, d in df.items():
        throughput = d['total_processed_requests'].diff().fillna(0)
        throughput_smooth = throughput.rolling(window=10, center=True).mean()
        plt.plot(d['time_seconds'], throughput_smooth, label=alg, alpha=0.8, linewidth=2)
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
