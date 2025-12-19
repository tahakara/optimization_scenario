# Zmax Request Primer Analizi

## Sistem Mimarisi

Aşağıdaki diyagramlar, yük dengeleme simülasyon sisteminin mimarisini ve çalışma akışını göstermektedir:

### Sistem Mimarisi Diyagramı
![Sistem Mimarisi](shared/png/Architecture_bg_w.png)

### Genel Sistem Diyagramı
![Sistem Diyagramı](shared/png/Diagram_bg_w.png)

### İş Akış Şeması
![İş Akış Şeması](shared/png/FlowChart_bg_w.png)

---

## Optimizasyon Problemi Formülasyonu

### Karar Değişkenleri

Optimizasyon probleminde aşağıdaki karar değişkenleri tanımlanmıştır:

| Değişken | Açıklama | Tip |
|----------|----------|-----|
| $x_{ij}$ | İstek $j$'nin sunucu $i$'ye atanma durumu (0 veya 1) | Binary |
| $w_i$ | Sunucu $i$'nin ağırlığı | Sürekli, $w_i > 0$ |
| $Q_i(t)$ | Sunucu $i$'nin $t$ zamanındaki kuyruk uzunluğu | Tamsayı, $Q_i \geq 0$ |
| $L_i(t)$ | Sunucu $i$'nin $t$ zamanındaki CPU yükü | Sürekli, $0 \leq L_i \leq C_i$ |

**Atama Kısıtı:**
$$
\sum_{i=1}^{S} x_{ij} = 1, \quad \forall j \in \{1, 2, ..., N\}
$$
Her istek sadece bir sunucuya atanır.

---

## Zmax Amaç Fonksiyonu

Zmax, maksimum yük altında algoritmaların performansını ölçen bir metrik olarak tanımlanır. 

### Temel Formül
$$
Z_{max} = \frac{P}{\bar{Q} \times \bar{W}}
$$

Burada:
- $P$: Toplam işlenen istek sayısı (total_processed_requests)
- $\bar{Q}$: Ortalama kuyruk uzunluğu (average_queue_length)
- $\bar{W}$: Ortalama bekleme süresi (average_wait_time)

### Genişletilmiş Matematiksel İfade

$$
Z_{max} = \frac{\sum_{i=1}^{S} \sum_{j=1}^{N_i} x_{ij}}{\left(\frac{1}{T} \int_{0}^{T} \sum_{i=1}^{S} Q_i(t) \, dt\right) \times \left(\frac{1}{P} \sum_{j=1}^{P} W_j\right)}
$$

Burada:
- $S$: Toplam sunucu sayısı (4)
- $N_i$: Sunucu $i$'ye atanan toplam istek sayısı
- $T$: Simülasyon süresi (600 saniye)
- $Q_i(t)$: Sunucu $i$'nin $t$ anındaki kuyruk uzunluğu
- $W_j$: İstek $j$'nin kuyrukta bekleme süresi

### Amaç Fonksiyonu (Maksimizasyon)

$$
\text{maximize} \quad Z_{max} = \frac{P}{\bar{Q} \times \bar{W}}
$$

Bu, aşağıdaki alt amaçlara eşdeğerdir:
1. **Maksimize:** İşlenen istek sayısı ($P$)
2. **Minimize:** Ortalama kuyruk uzunluğu ($\bar{Q}$)
3. **Minimize:** Ortalama bekleme süresi ($\bar{W}$)

### Alternatif Formülasyon (Throughput-Based)

$$
Z'_{max} = \frac{\text{Throughput}}{\text{Kayıp Oranı} + \epsilon} = \frac{P/T}{(N_{total} - P)/N_{total} + \epsilon}
$$

Burada $\epsilon$ küçük bir pozitif sayıdır (sıfıra bölme hatası önlemek için).

---

## Kısıtlar (Constraints)

Optimizasyon probleminde aşağıdaki kısıtlar tanımlanmıştır:

### Kısıt Özet Tablosu

| No | Kısıt Adı | Matematiksel İfade | Değer Aralığı |
|----|-----------|-------------------|---------------|
| $g_1$ | CPU Kapasitesi | $L_i(t) \leq C_i$ | $C_i = 100$ birim |
| $g_2$ | İstek Oranı | $\lambda(t) \leq \lambda_{max}$ | $133.3 - 333.3$ req/s |
| $g_3$ | Ağırlık Pozitifliği | $w_i > 0$ | $w_i \in \{5,3,2,1\}$ |
| $g_4, g_5$ | İşlem Hızı | $v_{min} \leq v_i \leq v_{max}$ | $[0.8, 1.5]$ |
| $g_6$ | Kuyruk Kapasitesi | $Q_i(t) \leq Q_{max}$ | $Q_{max} = \infty$ |
| $g_7$ | Zaman | $0 \leq t \leq T_{sim}$ | $T_{sim} = 600$ s |
| $g_8, g_9$ | CPU İhtiyacı | $CPU_{min} \leq c_j \leq CPU_{max}$ | $[5.0, 20.0]$ birim |

---

### 1. CPU Kapasitesi Kısıtı
Her sunucunun CPU kapasitesi sınırlıdır. Bu kapasite aşıldığında istekler kuyrukta bekler.

**Matematiksel İfade:**
$$
L_i(t) = \sum_{j \in A_i(t)} c_j \leq C_i, \quad \forall i \in \{1, 2, ..., S\}
$$

Burada:
- $S$: Toplam sunucu sayısı (4)
- $L_i(t)$: Sunucu $i$'nin $t$ zamanındaki toplam CPU yükü
- $A_i(t)$: Sunucu $i$'de $t$ anında aktif işlenen istekler kümesi
- $c_j$: İstek $j$'nin CPU ihtiyacı
- $C_i$: Sunucu $i$'nin maksimum CPU kapasitesi (100 birim)

**Kısıt Fonksiyonu:**
$$
g_1(x) = L_i(t) - C_i \leq 0, \quad \forall i \in \{1, ..., S\}
$$

**Lagrangian Katkısı:**
$$
\mathcal{L}_1 = \sum_{i=1}^{S} \mu_i \cdot \max(0, L_i(t) - C_i)
$$

### 2. İstek Oranı Kısıtı (Poisson Dağılımı)
Simülasyonda belirlenen sabit ve pik istek oranları, algoritmaların performansını etkiler. İstekler Poisson süreci ile modellenir.

**Matematiksel İfade:**
$$
\lambda(t) = \begin{cases} 
\lambda_{stabil} = \frac{8000}{60} \approx 133.3 \text{ req/s} & \text{normal zamanlar} \\
\lambda_{peak} = \frac{20000}{60} \approx 333.3 \text{ req/s} & \text{peak zamanlar}
\end{cases}
$$

**Peak Zaman Aralıkları:**
$$
t_{peak} \in [120, 180) \cup [360, 480) \text{ saniye}
$$

**İstekler Arası Süre (Exponential):**
$$
\tau \sim \text{Exp}(\lambda(t)), \quad f(\tau) = \lambda e^{-\lambda \tau}
$$

**Kısıt Fonksiyonu:**
$$
g_2(x) = \lambda(t) - \lambda_{max} \leq 0
$$

Burada $\lambda_{max} = 333.3$ req/s (peak dönemindeki maksimum oran).

### 3. Ağırlıklandırma Kısıtı (WRR ve WLC için)
WRR ve WLC algoritmalarında ağırlıklar, yük dağıtımını etkiler ve pozitif olmalıdır.

**Matematiksel İfade:**
$$
w_i > 0, \quad \forall i \in \{1, 2, ..., S\}
$$

**Normalizasyon:**
$$
\sum_{i=1}^{S} w_i = W_{total} = 5 + 3 + 2 + 1 = 11
$$

**Ağırlıklı Dağıtım Oranı:**
$$
p_i = \frac{w_i}{\sum_{k=1}^{S} w_k}, \quad \sum_{i=1}^{S} p_i = 1
$$

| Sunucu | Ağırlık ($w_i$) | Dağıtım Oranı ($p_i$) | İşlem Hızı ($v_i$) |
|--------|-----------------|----------------------|-------------------|
| 1 | 5 | 45.45% | 1.5 |
| 2 | 3 | 27.27% | 1.2 |
| 3 | 2 | 18.18% | 1.0 |
| 4 | 1 | 9.09% | 0.8 |

**Kısıt Fonksiyonu:**
$$
g_3(x) = -w_i < 0, \quad \forall i \in \{1, ..., S\}
$$

### 4. İşlem Hızı Kısıtı
Her sunucunun işlem hızı, ağırlıklarıyla ilişkilidir ve belirli sınırlar içinde kalmalıdır.

**Matematiksel İfade:**
$$
v_{min} \leq v_i \leq v_{max}, \quad \forall i \in \{1, 2, ..., S\}
$$

Burada:
- $v_i$: Sunucu $i$'nin işlem hızı faktörü
- $v_{min} = 0.8$ (minimum işlem hızı)
- $v_{max} = 1.5$ (maksimum işlem hızı)

**Efektif İşlem Süresi:**
$$
T_{eff,j} = \frac{T_{base,j}}{v_i}, \quad T_{base,j} \sim U(0.5, 3.0)
$$

**Kısıt Fonksiyonları:**
$$
g_4(x) = v_i - v_{max} \leq 0, \quad \forall i \in \{1, ..., S\}
$$
$$
g_5(x) = v_{min} - v_i \leq 0, \quad \forall i \in \{1, ..., S\}
$$

### 5. Kuyruk Kapasitesi Kısıtı
Her sunucunun kuyruğu sonsuz olmayabilir, bu durumda bir üst sınır belirlenmelidir.

**Matematiksel İfade:**
$$
Q_i(t) \leq Q_{max}, \quad \forall i \in \{1, 2, ..., S\}, \quad \forall t \in [0, T]
$$

Burada:
- $Q_i(t)$: Sunucu $i$'nin $t$ zamanındaki kuyruk uzunluğu
- $Q_{max}$: Maksimum kuyruk kapasitesi (simülasyonda $Q_{max} = \infty$)

**FIFO Kuyruk Dinamiği:**
$$
Q_i(t + \Delta t) = Q_i(t) + A_i(t) - D_i(t)
$$
- $A_i(t)$: $t$ anında gelen istek sayısı
- $D_i(t)$: $t$ anında işleme alınan istek sayısı

**Kısıt Fonksiyonu:**
$$
g_6(x) = Q_i(t) - Q_{max} \leq 0
$$

### 6. Zaman Kısıtı
Simülasyon süresi boyunca algoritmaların performansı değişebilir ve belirli bir süre içinde tamamlanmalıdır.

**Matematiksel İfade:**
$$
0 \leq t \leq T_{sim} = 600 \text{ saniye}
$$

**Simülasyon Time-Step:**
$$
\Delta t = 0.01 \text{ saniye}
$$

**Kısıt Fonksiyonu:**
$$
g_7(x) = t - T_{sim} \leq 0
$$

### 7. Request CPU İhtiyacı Kısıtı
Her request'in CPU ihtiyacı belirli bir aralıkta olmalıdır.

**Matematiksel İfade (Uniform Dağılım):**
$$
c_j \sim U(CPU_{min}, CPU_{max}), \quad \forall j \in \{1, 2, ..., N\}
$$

Burada:
- $c_j$: Request $j$'nin CPU ihtiyacı
- $CPU_{min} = 5.0$ birim
- $CPU_{max} = 20.0$ birim

**Beklenen CPU İhtiyacı:**
$$
E[c_j] = \frac{CPU_{min} + CPU_{max}}{2} = \frac{5.0 + 20.0}{2} = 12.5 \text{ birim}
$$

**Kısıt Fonksiyonları:**
$$
g_8(x) = c_j - CPU_{max} \leq 0, \quad \forall j
$$
$$
g_9(x) = CPU_{min} - c_j \leq 0, \quad \forall j
$$

---

## Lagrangian Formülasyonu

Tüm kısıtları Lagrangian çarpanları ile birleştiren genel formül:

$$
\mathcal{L}(x, \mu) = -Z_{max} + \sum_{k=1}^{9} \mu_k \cdot g_k(x)
$$

**Dual Problem:**
$$
\max_{\mu \geq 0} \min_{x} \mathcal{L}(x, \mu)
$$

**KKT Koşulları:**
1. $\nabla_x \mathcal{L} = 0$ (Stationarity)
2. $g_k(x) \leq 0$ (Primal Feasibility)
3. $\mu_k \geq 0$ (Dual Feasibility)
4. $\mu_k \cdot g_k(x) = 0$ (Complementary Slackness)

---

## Simülasyon Sonuçları ve Zmax Hesaplamaları

### Özet Tablo

| Algoritma | İşlenen İstek | Kayıp Oranı | Ort. Kuyruk | Ort. Bekleme (s) | Throughput | **Zmax** |
|-----------|--------------|-------------|-------------|-----------------|------------|----------|
| RR | 97,183 | %16.39 | 36,949.35 | 2,303.88 | 161.97 | **0.001142** |
| WRR | 92,412 | %20.50 | 27,613.01 | 2,104.17 | 154.02 | **0.001591** |
| LC | 98,158 | %15.55 | 37,384.42 | 2,325.04 | 163.60 | **0.001129** |
| WLC | 110,256 | %5.15 | 37,934.59 | 2,167.87 | 183.76 | **0.001341** |

### RR (Round Robin)
- İşlenen İstek: 97,183
- Kayıp Oranı: %16.39
- Ortalama Kuyruk Uzunluğu: 36,949.35
- Ortalama Bekleme Süresi: 2,303.88 saniye
- Throughput: 161.97 req/s
- **Zmax: 0.001142**

**Zmax Hesaplama:**
$$
Z_{max}^{RR} = \frac{97183}{36949.35 \times 2303.88} = \frac{97183}{85122134.5} \approx 0.001142
$$

- Sunucu Bazlı İşlenen İstekler:
  - Sunucu 1: 24,448
  - Sunucu 2: 24,504
  - Sunucu 3: 24,492
  - Sunucu 4: 24,463

### WRR (Weighted Round Robin)
- İşlenen İstek: 92,412
- Kayıp Oranı: %20.50
- Ortalama Kuyruk Uzunluğu: 27,613.01
- Ortalama Bekleme Süresi: 2,104.17 saniye
- Throughput: 154.02 req/s
- **Zmax: 0.001591** ⭐ (En yüksek)

**Zmax Hesaplama:**
$$
Z_{max}^{WRR} = \frac{92412}{27613.01 \times 2104.17} = \frac{92412}{58102289.2} \approx 0.001591
$$

- Sunucu Bazlı İşlenen İstekler:
  - Sunucu 1: 42,030
  - Sunucu 2: 25,159
  - Sunucu 3: 17,049
  - Sunucu 4: 8,695

### LC (Least Connections)
- İşlenen İstek: 98,158
- Kayıp Oranı: %15.55
- Ortalama Kuyruk Uzunluğu: 37,384.42
- Ortalama Bekleme Süresi: 2,325.04 saniye
- Throughput: 163.60 req/s
- **Zmax: 0.001129**

**Zmax Hesaplama:**
$$
Z_{max}^{LC} = \frac{98158}{37384.42 \times 2325.04} = \frac{98158}{86920227.4} \approx 0.001129
$$

- Sunucu Bazlı İşlenen İstekler:
  - Sunucu 1: 24,576
  - Sunucu 2: 24,662
  - Sunucu 3: 24,701
  - Sunucu 4: 24,524

### WLC (Weighted Least Connections)
- İşlenen İstek: 110,256
- Kayıp Oranı: %5.15
- Ortalama Kuyruk Uzunluğu: 37,934.59
- Ortalama Bekleme Süresi: 2,167.87 saniye
- Throughput: 183.76 req/s
- **Zmax: 0.001341**

**Zmax Hesaplama:**
$$
Z_{max}^{WLC} = \frac{110256}{37934.59 \times 2167.87} = \frac{110256}{82233011.2} \approx 0.001341
$$

- Sunucu Bazlı İşlenen İstekler:
  - Sunucu 1: 34,774
  - Sunucu 2: 29,027
  - Sunucu 3: 25,840
  - Sunucu 4: 21,433

---

## Görselleştirme
Simülasyon sonuçlarına ait grafikler aşağıdaki gibidir:

1. **Toplam Kuyruk Uzunluğu:**
   ![Toplam Kuyruk Uzunluğu](simulasyon_grafikleri/queue_length.png)

2. **Kümülatif İşlenen İstek Sayısı:**
   ![Kümülatif İşlenen İstek Sayısı](simulasyon_grafikleri/processed_requests.png)

3. **RR vs WRR CPU Kullanımı:**
   ![RR vs WRR CPU Kullanımı](simulasyon_grafikleri/rr_vs_wrr_cpu.png)

4. **LC vs WLC CPU Kullanımı:**
   ![LC vs WLC CPU Kullanımı](simulasyon_grafikleri/lc_vs_wlc_cpu.png)

5. **Ortalama Bekleme Süresi:**
   ![Ortalama Bekleme Süresi](simulasyon_grafikleri/average_wait_time.png)

6. **Sunucu Bazlı CPU Kullanımı:**
   - RR: ![RR Sunucu Bazlı CPU](simulasyon_grafikleri/rr_server_cpu.png)
   - WRR: ![WRR Sunucu Bazlı CPU](simulasyon_grafikleri/wrr_server_cpu.png)
   - LC: ![LC Sunucu Bazlı CPU](simulasyon_grafikleri/lc_server_cpu.png)
   - WLC: ![WLC Sunucu Bazlı CPU](simulasyon_grafikleri/wlc_server_cpu.png)

7. **Throughput (İşlenen İstek/Saniye):**
   ![Throughput](simulasyon_grafikleri/throughput.png)

---

## Sistem Akış Analizi

### Yük Dengeleme İş Akışı
Aşağıdaki akış şeması, yük dengeleme algoritmalarının nasıl çalıştığını ve karar verme süreçlerini göstermektedir:

<!-- ![Yük Dengeleme İş Akışı](shared/png/FlowChart.png) -->

Bu akış şeması şunları gösterir:
- İsteklerin sisteme nasıl geldiği
- Algoritmaların nasıl sunucu seçtiği
- CPU kapasitesi kontrollerinin nasıl yapıldığı
- Kuyruk yönetimi süreçleri
- İstek işleme ve tamamlanma aşamaları

---

## Çözüm Grafiği
Aşağıdaki grafik, her algoritma için Zmax değerlerini göstermektedir:

![Zmax Grafiği](simulasyon_grafikleri/zmax_graph.png)

---

## Çözüm Noktaları ve Zmax Analizi

### Zmax Sıralaması
$$
Z_{max}^{WRR} > Z_{max}^{WLC} > Z_{max}^{RR} > Z_{max}^{LC}
$$
$$
0.001591 > 0.001341 > 0.001142 > 0.001129
$$

### Algoritma Bazlı Analiz

1. **WRR (Weighted Round Robin) - En Yüksek Zmax: 0.001591** ⭐
   - En düşük ortalama kuyruk uzunluğu (27,613)
   - Düşük bekleme süresi (2,104 s)
   - Yüksek kayıp oranı (%20.50) dezavantajı
   - **Zmax açısından optimal**, ancak toplam işlenen istek düşük

2. **WLC (Weighted Least Connections) - Zmax: 0.001341**
   - En yüksek işlenen istek sayısı (110,256)
   - En düşük kayıp oranı (%5.15)
   - Orta düzey kuyruk ve bekleme süresi
   - **Pratikte en iyi performans** (throughput + kayıp dengesinde)

3. **RR (Round Robin) - Zmax: 0.001142**
   - Dengeli yük dağıtımı (sunucular arası ~%0.2 fark)
   - Basit implementasyon
   - Orta düzey performans metrikleri

4. **LC (Least Connections) - En Düşük Zmax: 0.001129**
   - En dengeli sunucu dağılımı
   - Yüksek kuyruk uzunluğu (37,384)
   - CPU kapasitesini dikkate almaz

### Pareto Optimal Çözümler

Multi-objective optimizasyon perspektifinden:

| Hedef | En İyi Algoritma | Değer |
|-------|-----------------|-------|
| Max Zmax | WRR | 0.001591 |
| Max İşlenen İstek | WLC | 110,256 |
| Min Kayıp Oranı | WLC | %5.15 |
| Min Kuyruk | WRR | 27,613 |
| Min Bekleme | WRR | 2,104 s |
| Max Throughput | WLC | 183.76 req/s |

### Trade-off Analizi

**WRR vs WLC:**
$$
\frac{Z_{max}^{WRR}}{Z_{max}^{WLC}} = \frac{0.001591}{0.001341} \approx 1.186 \quad (+18.6\%)
$$

$$
\frac{P^{WLC}}{P^{WRR}} = \frac{110256}{92412} \approx 1.193 \quad (+19.3\%)
$$

WRR, Zmax'ta %18.6 daha iyi; WLC, işlenen istekte %19.3 daha iyi.

---

## Sistem Mimarisi ve Bileşenler

### Mimari Genel Bakış
<!-- ![Mimari Diyagram](shared/png/Architecture.png) -->

Yukarıdaki mimari diyagram, sistemin ana bileşenlerini göstermektedir:

1. **İstek Oluşturucu (Request Generator):**
   - Poisson dağılımına göre rastgele istekler üretir
   - Stabil ve peak yük modlarını destekler
   - Her istek için CPU ihtiyacı ve işlem süresi belirler

2. **Yük Dengeleyici (Load Balancer):**
   - Dört farklı algoritma (RR, WRR, LC, WLC) destekler
   - İstekleri sunuculara dağıtır
   - CPU kapasitesi ve kuyruk durumunu kontrol eder

3. **Sunucu Havuzu (Server Pool):**
   - 4 sunucu içerir
   - Her sunucunun kendine özgü ağırlık ve işlem hızı vardır
   - CPU kapasitesi: 100 birim/sunucu

4. **Kuyruk Yönetimi (Queue Management):**
   - FIFO (First In First Out) kuyruk yapısı
   - Dinamik kuyruk uzunluğu takibi
   - CPU kapasitesi kontrolü ile akıllı kuyruk yönetimi

5. **Metrik Toplayıcı (Metrics Collector):**
   - Gerçek zamanlı performans metrikleri toplar
   - CSV formatında sonuçları kaydeder
   - Görselleştirme için veri hazırlar

### Sistem Diyagramı
<!-- ![Sistem Diyagramı](shared/png/Diagram.png) -->

Sistem diyagramı, bileşenler arası iletişimi ve veri akışını detaylı olarak gösterir.

---

## Sonuç ve Optimizasyon Önerileri

### Zmax Analizi Sonuçları

Zmax metriği ile yapılan analiz, **WRR algoritmasının en yüksek Zmax değerine** (0.001591) sahip olduğunu göstermektedir. Ancak bu sonuç dikkatle yorumlanmalıdır:

#### Zmax Formülünün Özellikleri:
$$
Z_{max} = \frac{P}{\bar{Q} \times \bar{W}}
$$

- **Yüksek Zmax:** Düşük kuyruk uzunluğu ve bekleme süresi ile orantılı
- **WRR paradoksu:** Yüksek kayıp oranı (%20.50) kuyruk uzunluğunu düşürür → Zmax artar
- **WLC avantajı:** En fazla istek işler (%5.15 kayıp) ancak bu durum kuyruğu artırır

### Senaryo Bazlı Öneriler

| Senaryo | Önerilen Algoritma | Sebep |
|---------|-------------------|-------|
| Maksimum Throughput | WLC | 183.76 req/s, %5.15 kayıp |
| Minimum Kayıp | WLC | En düşük kayıp oranı |
| Minimum Bekleme | WRR | 2,104 s ortalama bekleme |
| Maksimum Zmax | WRR | 0.001591 (formül bazlı optimum) |
| Dengeli Yük | RR veya LC | Sunucular arası eşit dağılım |

### Önerilen İyileştirmeler

1. **Dinamik Ağırlıklandırma:**
   $$
   w_i(t) = w_i^{base} \times \left(1 - \frac{L_i(t)}{C_i}\right)
   $$
   CPU yüküne göre anlık ağırlık ayarlaması

2. **Hibrit Algoritma:**
   $$
   \text{score}_i = \alpha \cdot \frac{Q_i}{Q_{max}} + \beta \cdot \frac{L_i}{C_i} + \gamma \cdot \frac{1}{w_i}
   $$
   Kuyruk, CPU ve ağırlık kombinasyonu

3. **Adaptive Peak Management:**
   - Peak dönemlerde ağırlıkları otomatik ayarlama
   - CPU threshold bazlı istek reddi

### Final Değerlendirme

| Metrik | En İyi | Algoritma | Değer |
|--------|--------|-----------|-------|
| **Zmax** | ✅ | WRR | 0.001591 |
| **Pratik Performans** | ✅ | WLC | 110,256 işlenen istek |
| **Basitlik** | ✅ | RR | Kolay implementasyon |
| **Denge** | ✅ | LC | Eşit sunucu kullanımı |

**Sonuç:** 
- **Zmax optimizasyonu** için → **WRR** tercih edilmeli
- **Gerçek dünya performansı** için → **WLC** tercih edilmeli
- **Trade-off:** Zmax vs. Toplam İşlenen İstek arasında denge kurulmalı

Simülasyon parametreleri ve kısıtlar, algoritmaların performansını önemli ölçüde etkiler. Yukarıdaki mimari diyagramlar ve akış şemaları, sistemin nasıl çalıştığını ve optimize edilebileceğini anlamak için önemli bir referans sağlar.

---

## Algoritma Bazlı Zmax Request Matematiksel Formülasyonları

Her yük dengeleme algoritması için ayrı ayrı Zmax Request optimizasyon problemleri aşağıda formüle edilmiştir.

---

### 1. Round Robin (RR) - Zmax Request Formülasyonu

#### Algoritma Tanımı
Round Robin, istekleri sırayla sunuculara dağıtır. Her sunucu eşit sayıda istek alır.

#### Sunucu Seçim Fonksiyonu
$$
i^*(j) = (j - 1) \mod S + 1
$$

Burada:
- $i^*(j)$: İstek $j$ için seçilen sunucu indeksi
- $j$: İstek numarası
- $S$: Toplam sunucu sayısı (4)

#### Atama Matrisi
$$
x_{ij}^{RR} = \begin{cases} 
1 & \text{eğer } i = (j-1) \mod S + 1 \\
0 & \text{aksi halde}
\end{cases}
$$

#### Zmax Amaç Fonksiyonu (RR)
$$
\boxed{Z_{max}^{RR} = \frac{\sum_{i=1}^{S} \sum_{j=1}^{N} x_{ij}^{RR}}{\left(\frac{1}{T} \int_{0}^{T} \sum_{i=1}^{S} Q_i^{RR}(t) \, dt\right) \times \left(\frac{1}{P^{RR}} \sum_{j=1}^{P^{RR}} W_j^{RR}\right)}}
$$

#### Özel Kısıtlar (RR)
$$
\sum_{j=1}^{N} x_{ij}^{RR} = \frac{N}{S}, \quad \forall i \in \{1, ..., S\} \quad \text{(Eşit dağılım)}
$$

#### Kuyruk Dinamiği (RR)
$$
Q_i^{RR}(t + \Delta t) = Q_i^{RR}(t) + \mathbb{1}_{[i = (n(t)-1) \mod S + 1]} - D_i^{RR}(t)
$$

Burada $n(t)$: $t$ anına kadar gelen toplam istek sayısı

#### Hesaplanan Değer
$$
Z_{max}^{RR} = \frac{97183}{36949.35 \times 2303.88} = \mathbf{0.001142}
$$

---

### 2. Weighted Round Robin (WRR) - Zmax Request Formülasyonu

#### Algoritma Tanımı
Weighted Round Robin, sunuculara ağırlıklarına orantılı olarak istek dağıtır.

#### Ağırlık Vektörü
$$
\mathbf{w} = [w_1, w_2, w_3, w_4] = [5, 3, 2, 1]
$$

#### Ağırlık Tekerleği (Weight Wheel)
$$
\mathcal{W} = \{\underbrace{1, 1, 1, 1, 1}_{w_1=5}, \underbrace{2, 2, 2}_{w_2=3}, \underbrace{3, 3}_{w_3=2}, \underbrace{4}_{w_4=1}\}
$$

#### Sunucu Seçim Fonksiyonu
$$
i^*(j) = \mathcal{W}[(j-1) \mod W_{total}], \quad W_{total} = \sum_{i=1}^{S} w_i = 11
$$

#### Atama Matrisi
$$
x_{ij}^{WRR} = \begin{cases} 
1 & \text{eğer } i = \mathcal{W}[(j-1) \mod W_{total}] \\
0 & \text{aksi halde}
\end{cases}
$$

#### Zmax Amaç Fonksiyonu (WRR)
$$
\boxed{Z_{max}^{WRR} = \frac{\sum_{i=1}^{S} \sum_{j=1}^{N} x_{ij}^{WRR}}{\left(\frac{1}{T} \int_{0}^{T} \sum_{i=1}^{S} Q_i^{WRR}(t) \, dt\right) \times \left(\frac{1}{P^{WRR}} \sum_{j=1}^{P^{WRR}} W_j^{WRR}\right)}}
$$

#### Özel Kısıtlar (WRR)
$$
\frac{\sum_{j=1}^{N} x_{ij}^{WRR}}{\sum_{j=1}^{N} x_{kj}^{WRR}} = \frac{w_i}{w_k}, \quad \forall i, k \in \{1, ..., S\} \quad \text{(Ağırlık orantısı)}
$$

#### Beklenen Dağılım Oranı
$$
E\left[\frac{N_i}{N}\right] = \frac{w_i}{\sum_{k=1}^{S} w_k} = p_i
$$

| Sunucu $i$ | Ağırlık $w_i$ | Beklenen Oran $p_i$ | Gerçekleşen |
|------------|---------------|---------------------|-------------|
| 1 | 5 | 45.45% | 45.48% |
| 2 | 3 | 27.27% | 27.22% |
| 3 | 2 | 18.18% | 18.45% |
| 4 | 1 | 9.09% | 9.41% |

#### İşlem Hızı Etkisi
$$
T_{eff,j}^{WRR} = \frac{T_{base,j}}{v_i}, \quad v_i \in \{1.5, 1.2, 1.0, 0.8\}
$$

#### Hesaplanan Değer
$$
Z_{max}^{WRR} = \frac{92412}{27613.01 \times 2104.17} = \mathbf{0.001591} \quad \text{⭐ EN YÜKSEK}
$$

---

### 3. Least Connections (LC) - Zmax Request Formülasyonu

#### Algoritma Tanımı
Least Connections, en az aktif bağlantıya sahip sunucuya istek yönlendirir.

#### Aktif Bağlantı Sayısı
$$
C_i(t) = |Q_i(t)| + |A_i(t)|
$$

Burada:
- $|Q_i(t)|$: Sunucu $i$'nin kuyruk uzunluğu
- $|A_i(t)|$: Sunucu $i$'de aktif işlenen istek sayısı

#### Sunucu Seçim Fonksiyonu
$$
i^*(j, t) = \arg\min_{i \in \{1,...,S\}} C_i(t)
$$

Eşitlik durumunda:
$$
i^*(j, t) = \min\{i : C_i(t) = \min_{k} C_k(t)\}
$$

#### Atama Matrisi
$$
x_{ij}^{LC}(t) = \begin{cases} 
1 & \text{eğer } i = \arg\min_{k} C_k(t_j) \\
0 & \text{aksi halde}
\end{cases}
$$

#### Zmax Amaç Fonksiyonu (LC)
$$
\boxed{Z_{max}^{LC} = \frac{\sum_{i=1}^{S} \sum_{j=1}^{N} x_{ij}^{LC}}{\left(\frac{1}{T} \int_{0}^{T} \sum_{i=1}^{S} Q_i^{LC}(t) \, dt\right) \times \left(\frac{1}{P^{LC}} \sum_{j=1}^{P^{LC}} W_j^{LC}\right)}}
$$

#### Özel Kısıtlar (LC)
**Greedy Seçim Kısıtı:**
$$
C_{i^*}(t_j) \leq C_k(t_j), \quad \forall k \in \{1, ..., S\}, \quad \forall j
$$

**Yük Dengeleme Özelliği:**
$$
|C_i(t) - C_k(t)| \leq 1, \quad \forall i, k \in \{1, ..., S\}, \quad \text{(yaklaşık)}
$$

#### Kuyruk Dinamiği (LC)
$$
Q_i^{LC}(t + \Delta t) = Q_i^{LC}(t) + \mathbb{1}_{[i = i^*(n(t), t)]} - D_i^{LC}(t)
$$

#### Hesaplanan Değer
$$
Z_{max}^{LC} = \frac{98158}{37384.42 \times 2325.04} = \mathbf{0.001129}
$$

---

### 4. Weighted Least Connections (WLC) - Zmax Request Formülasyonu

#### Algoritma Tanımı
Weighted Least Connections, aktif bağlantı sayısını ağırlıklarla normalize ederek en uygun sunucuyu seçer.

#### Efektif Yük Metriği
$$
E_i(t) = \frac{C_i(t)}{w_i \cdot v_i} + \alpha \cdot \frac{L_i(t)}{C_i^{max}}
$$

Burada:
- $C_i(t)$: Aktif bağlantı sayısı
- $w_i$: Sunucu ağırlığı
- $v_i$: İşlem hızı
- $L_i(t)$: CPU yükü
- $C_i^{max}$: CPU kapasitesi (100 birim)
- $\alpha = 5$: CPU yükü ağırlık faktörü

#### Sunucu Seçim Fonksiyonu
$$
i^*(j, t) = \arg\min_{i \in \{1,...,S\}} E_i(t)
$$

#### Dinamik Ağırlık Güncelleme
$$
w_i(t) = \max\left(1, C_i^{max} - L_i(t)\right)
$$

#### Atama Matrisi
$$
x_{ij}^{WLC}(t) = \begin{cases} 
1 & \text{eğer } i = \arg\min_{k} E_k(t_j) \\
0 & \text{aksi halde}
\end{cases}
$$

#### Zmax Amaç Fonksiyonu (WLC)
$$
\boxed{Z_{max}^{WLC} = \frac{\sum_{i=1}^{S} \sum_{j=1}^{N} x_{ij}^{WLC}}{\left(\frac{1}{T} \int_{0}^{T} \sum_{i=1}^{S} Q_i^{WLC}(t) \, dt\right) \times \left(\frac{1}{P^{WLC}} \sum_{j=1}^{P^{WLC}} W_j^{WLC}\right)}}
$$

#### Özel Kısıtlar (WLC)
**Ağırlıklı Yük Dengeleme:**
$$
\frac{C_i(t)}{w_i} \approx \frac{C_k(t)}{w_k}, \quad \forall i, k \quad \text{(hedef)}
$$

**CPU-Aware Seçim:**
$$
L_{i^*}(t) + c_j \leq C_{i^*}^{max} \quad \text{(tercih edilen)}
$$

**Kapasite Kontrolü:**
$$
\text{if } L_i(t) + c_j > C_i^{max} \Rightarrow \text{alternatif sunucu ara veya kuyruğa ekle}
$$

#### Throughput Maksimizasyonu
$$
\text{Throughput}^{WLC} = \frac{P^{WLC}}{T} = \frac{110256}{600} = 183.76 \text{ req/s}
$$

#### Hesaplanan Değer
$$
Z_{max}^{WLC} = \frac{110256}{37934.59 \times 2167.87} = \mathbf{0.001341}
$$

---

## Karşılaştırmalı Zmax Formül Özeti

| Algoritma | Seçim Kriteri | Zmax Formülü | Değer |
|-----------|---------------|--------------|-------|
| **RR** | $i = (j-1) \mod S + 1$ | $Z_{max}^{RR} = \frac{P^{RR}}{\bar{Q}^{RR} \times \bar{W}^{RR}}$ | 0.001142 |
| **WRR** | $i = \mathcal{W}[(j-1) \mod W_{total}]$ | $Z_{max}^{WRR} = \frac{P^{WRR}}{\bar{Q}^{WRR} \times \bar{W}^{WRR}}$ | **0.001591** |
| **LC** | $i = \arg\min_k C_k(t)$ | $Z_{max}^{LC} = \frac{P^{LC}}{\bar{Q}^{LC} \times \bar{W}^{LC}}$ | 0.001129 |
| **WLC** | $i = \arg\min_k E_k(t)$ | $Z_{max}^{WLC} = \frac{P^{WLC}}{\bar{Q}^{WLC} \times \bar{W}^{WLC}}$ | 0.001341 |

### Genel Zmax Optimizasyon Problemi

$$
\begin{aligned}
\text{maximize} \quad & Z_{max}^{ALG} = \frac{P^{ALG}}{\bar{Q}^{ALG} \times \bar{W}^{ALG}} \\
\text{subject to} \quad & \sum_{i=1}^{S} x_{ij} = 1, \quad \forall j \\
& L_i(t) \leq C_i, \quad \forall i, t \\
& w_i > 0, \quad \forall i \\
& v_{min} \leq v_i \leq v_{max}, \quad \forall i \\
& Q_i(t) \geq 0, \quad \forall i, t \\
& x_{ij} \in \{0, 1\}, \quad \forall i, j \\
& ALG \in \{RR, WRR, LC, WLC\}
\end{aligned}
$$

---

### Değişken ve Parametre Açıklamaları

#### Amaç Fonksiyonu Değişkenleri

| Sembol | Açıklama | Birim | Değer/Aralık |
|--------|----------|-------|--------------|
| $Z_{max}^{ALG}$ | Algoritma $ALG$ için Zmax performans metriği | - | $[0, \infty)$ |
| $P^{ALG}$ | Algoritma $ALG$ ile toplam işlenen istek sayısı | adet | Simülasyonda: 92,412 - 110,256 |
| $\bar{Q}^{ALG}$ | Algoritma $ALG$ için ortalama kuyruk uzunluğu | istek | Simülasyonda: 27,613 - 37,935 |
| $\bar{W}^{ALG}$ | Algoritma $ALG$ için ortalama bekleme süresi | saniye | Simülasyonda: 2,104 - 2,325 |

#### Karar Değişkenleri

| Sembol | Açıklama | Tip | Değer/Aralık |
|--------|----------|-----|--------------|
| $x_{ij}$ | İstek $j$'nin sunucu $i$'ye atanıp atanmadığı | Binary | $\{0, 1\}$ |
| $w_i$ | Sunucu $i$'nin ağırlığı | Tamsayı | $w_i \in \{5, 3, 2, 1\}$ |
| $v_i$ | Sunucu $i$'nin işlem hızı faktörü | Sürekli | $v_i \in \{1.5, 1.2, 1.0, 0.8\}$ |

#### Durum Değişkenleri (Zamana Bağlı)

| Sembol | Açıklama | Birim | Değer/Aralık |
|--------|----------|-------|--------------|
| $Q_i(t)$ | Sunucu $i$'nin $t$ anındaki kuyruk uzunluğu | istek | $Q_i \geq 0$ |
| $L_i(t)$ | Sunucu $i$'nin $t$ anındaki CPU yükü | birim | $0 \leq L_i \leq 100$ |
| $C_i(t)$ | Sunucu $i$'nin $t$ anındaki aktif bağlantı sayısı | adet | $C_i = Q_i + A_i$ |
| $A_i(t)$ | Sunucu $i$'de $t$ anında işlenen istek sayısı | adet | $A_i \geq 0$ |

#### Sabit Parametreler

| Sembol | Açıklama | Değer |
|--------|----------|-------|
| $S$ | Toplam sunucu sayısı | 4 |
| $N$ | Toplam gelen istek sayısı | ~116,000 |
| $T$ | Simülasyon süresi | 600 saniye |
| $\Delta t$ | Zaman adımı (time-step) | 0.01 saniye |
| $C_i$ | Sunucu $i$'nin maksimum CPU kapasitesi | 100 birim |
| $v_{min}$ | Minimum işlem hızı | 0.8 |
| $v_{max}$ | Maksimum işlem hızı | 1.5 |
| $W_{total}$ | Toplam ağırlık (WRR için) | $\sum w_i = 11$ |

#### İstek Parametreleri

| Sembol | Açıklama | Dağılım | Değer/Aralık |
|--------|----------|---------|--------------|
| $c_j$ | İstek $j$'nin CPU ihtiyacı | $U(5, 20)$ | 5.0 - 20.0 birim |
| $T_{base,j}$ | İstek $j$'nin temel işlem süresi | $U(0.5, 3.0)$ | 0.5 - 3.0 saniye |
| $W_j$ | İstek $j$'nin kuyrukta bekleme süresi | - | $\geq 0$ saniye |
| $\lambda(t)$ | $t$ anındaki istek geliş oranı | Poisson | 133.3 - 333.3 req/s |

#### İndeksler

| Sembol | Açıklama | Aralık |
|--------|----------|--------|
| $i$ | Sunucu indeksi | $i \in \{1, 2, 3, 4\}$ |
| $j$ | İstek indeksi | $j \in \{1, 2, ..., N\}$ |
| $t$ | Zaman indeksi | $t \in [0, T]$ |
| $ALG$ | Algoritma türü | $ALG \in \{RR, WRR, LC, WLC\}$ |

#### Algoritma-Spesifik Değişkenler

| Sembol | Algoritma | Açıklama |
|--------|-----------|----------|
| $\mathcal{W}$ | WRR | Ağırlık tekerleği dizisi: $\{1,1,1,1,1,2,2,2,3,3,4\}$ |
| $E_i(t)$ | WLC | Efektif yük metriği: $\frac{C_i(t)}{w_i \cdot v_i} + \alpha \cdot \frac{L_i(t)}{C_i^{max}}$ |
| $\alpha$ | WLC | CPU yükü ağırlık faktörü: 5 |
| $p_i$ | WRR/WLC | Sunucu $i$'nin dağılım oranı: $\frac{w_i}{\sum_k w_k}$ |

#### Kısıt Açıklamaları

| Kısıt | Matematiksel İfade | Açıklama |
|-------|-------------------|----------|
| Atama | $\sum_{i=1}^{S} x_{ij} = 1$ | Her istek tam olarak bir sunucuya atanır |
| CPU Kapasitesi | $L_i(t) \leq C_i$ | Sunucu CPU yükü kapasiteyi aşamaz |
| Ağırlık Pozitifliği | $w_i > 0$ | Tüm ağırlıklar pozitif olmalı |
| İşlem Hızı | $v_{min} \leq v_i \leq v_{max}$ | İşlem hızı belirli aralıkta olmalı |
| Kuyruk Pozitifliği | $Q_i(t) \geq 0$ | Kuyruk uzunluğu negatif olamaz |
| Binary Atama | $x_{ij} \in \{0, 1\}$ | Atama değişkeni binary |