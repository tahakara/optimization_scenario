# Zmax Request Primer Analizi

## Zmax Fonksiyonu
Zmax, maksimum yük altında algoritmaların performansını ölçen bir metrik olarak tanımlanır. Aşağıdaki formül kullanılmıştır:

$$
Z_{max} = \frac{\text{total_processed_requests}}{\text{total_queue_length} \times \text{average_wait_time}}
$$

Bu fonksiyon, işlenen istek sayısını artırırken kuyruk uzunluğunu ve bekleme süresini minimize eden algoritmayı belirler.

---

## Kısıtlar
1. **CPU Kapasitesi:** Her sunucunun CPU kapasitesi sınırlıdır (örneğin, 100 birim). Bu kapasite aşıldığında istekler kuyrukta bekler.
2. **İstek Oranı:** Simülasyonda belirlenen sabit ve pik istek oranları, algoritmaların performansını etkiler.
3. **Ağırlıklandırma:** WRR ve WLC algoritmalarında ağırlıklar, yük dağıtımını etkiler.
4. **Zaman:** Simülasyon süresi boyunca algoritmaların performansı değişebilir.

---

## Simülasyon Sonuçları

### RR (Round Robin)
- İşlenen İstek: 97,907
- Kayıp Oranı: %15.75
- Ortalama Bekleme Süresi: 2339.92 saniye
- Throughput: 163.18 req/s
- Sunucu Bazlı İşlenen İstekler:
  - Sunucu 1: 24,448
  - Sunucu 2: 24,504
  - Sunucu 3: 24,492
  - Sunucu 4: 24,463

### WRR (Weighted Round Robin)
- İşlenen İstek: 92,933
- Kayıp Oranı: %20.03
- Ortalama Bekleme Süresi: 2144.63 saniye
- Throughput: 154.89 req/s
- Sunucu Bazlı İşlenen İstekler:
  - Sunucu 1: 42,030
  - Sunucu 2: 25,159
  - Sunucu 3: 17,049
  - Sunucu 4: 8,695

### LC (Least Connections)
- İşlenen İstek: 98,463
- Kayıp Oranı: %15.27
- Ortalama Bekleme Süresi: 2349.48 saniye
- Throughput: 164.10 req/s
- Sunucu Bazlı İşlenen İstekler:
  - Sunucu 1: 24,576
  - Sunucu 2: 24,662
  - Sunucu 3: 24,701
  - Sunucu 4: 24,524

### WLC (Weighted Least Connections)
- İşlenen İstek: 111,074
- Kayıp Oranı: %4.42
- Ortalama Bekleme Süresi: 2200.47 saniye
- Throughput: 185.12 req/s
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

## Çözüm Grafiği
Aşağıdaki grafik, her algoritma için Zmax değerlerini göstermektedir:

![Zmax Grafiği](simulasyon_grafikleri/zmax_graph.png)

---

## Çözüm Noktaları
1. **RR (Round Robin):**
   - Dengeli yük dağıtımı sağlar ancak CPU kapasitesini dikkate almaz.
   - Zmax değeri orta seviyededir.

2. **WRR (Weighted Round Robin):**
   - Ağırlıklandırma sayesinde daha verimli yük dağıtımı yapar.
   - Zmax değeri genellikle RR'den yüksektir.

3. **LC (Least Connections):**
   - Kuyruk uzunluğunu minimize eder.
   - Zmax değeri, düşük bekleme süresi nedeniyle yüksektir.

4. **WLC (Weighted Least Connections):**
   - Hem kuyruk uzunluğunu hem de CPU yükünü dikkate alır.
   - Zmax değeri, doğru ağırlıklandırma ile en yüksek olabilir.

---

## Sonuç
Zmax analizi, WLC algoritmasının doğru ağırlıklandırma ve CPU yükü yönetimi ile en iyi performansı sağlayabileceğini göstermektedir. Ancak, simülasyon parametreleri ve kısıtlar, algoritmaların performansını önemli ölçüde etkiler.