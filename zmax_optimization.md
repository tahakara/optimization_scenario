# Zmax Request Optimizasyon Analizi

Bu bölümde, simülasyon analizlerinden elde edilen bulgulara ve WRR algoritmasının üstün performansına dayanarak, sistemdeki CPU miktarına göre maksimum işlenebilecek istek (Zmax) için optimizasyon amaç ve kısıt fonksiyonları oluşturulmuştur.

## 1. Problem Tanımı
Amaç, toplam CPU kapasitesi ve sunucu ağırlıklarına göre, sistemin birim zamanda işleyebileceği maksimum istek sayısını (Zmax) bulmaktır. Analizler sonucunda WRR algoritmasının en iyi performansı verdiği tespit edilmiştir.

## 2. Karar Değişkenleri
- $z_{max}$: Maksimum işlenebilecek istek sayısı (birim zamanda)
- $x_i$: Sunucu $i$'ye atanacak istek sayısı (birim zamanda)
- $w_i$: Sunucu $i$'nin WRR ağırlığı
- $C_i$: Sunucu $i$'nin CPU kapasitesi (unit)
- $r_{avg}$: Ortalama bir isteğin CPU ihtiyacı (unit)

## 3. Amaç Fonksiyonu

Amaç, toplam işlenen istek sayısını maksimize etmektir. Yani, sistemin birim zamanda işleyebileceği en fazla istek sayısını bulmak istiyoruz.

### Amaç Fonksiyonu Doğrusal mı?
Evet, bu amaç fonksiyonu **doğrusaldır**. Çünkü $z_{max}$ ve $x_i$ değişkenleri birinci dereceden (lineer) olarak fonksiyonda yer alır ve aralarında çarpma, üstel, logaritmik gibi doğrusal olmayan bir ilişki yoktur. Sadece toplama ve çarpma işlemleri vardır.

$$
\max z_{max} = \sum_{i=1}^{N} x_i
$$

Burada $x_i$'ler de $z_{max}$'a doğrusal olarak bağlıdır (aşağıda açıklanacak).

---

## Değişkenlerin Açıklamaları (Temel Düzeyde)

- **$z_{max}$**: Sistemin birim zamanda (örneğin 1 saniyede) işleyebileceği maksimum toplam istek (request) sayısıdır. Yani, "en fazla kaç isteği aynı anda işleyebilirim?" sorusunun cevabıdır.

- **$x_i$**: $i$ numaralı sunucuya (server) atanacak istek sayısıdır. Yani, toplam isteklerin sunuculara dağıtılmış hali. Her sunucuya farklı sayıda istek atanabilir.

- **$w_i$**: $i$ numaralı sunucunun WRR (Weighted Round Robin) algoritmasındaki ağırlığıdır. Ağırlık, o sunucunun daha fazla veya daha az istek almasını sağlar. Büyük ağırlık = daha çok istek.

- **$C_i$**: $i$ numaralı sunucunun toplam CPU kapasitesidir (örneğin 100 birim). Bir sunucu, kapasitesinden fazla yük alamaz.

- **$r_{avg}$**: Ortalama bir isteğin (request) CPU ihtiyacıdır. Yani, bir isteği işlemek için ortalama ne kadar CPU gerekir?

- **$N$**: Toplam sunucu sayısıdır.

---

## Fonksiyonun Yapısı ve Yorumu

- Amaç fonksiyonu, $z_{max}$'ı (veya toplam $x_i$'yi) **maksimize etmek** ister. Yani, sistemin kapasitesini en verimli şekilde kullanarak en fazla isteği işlemek hedeflenir.
- Kısıtlar ise, her sunucunun kapasitesini aşmamasını ve isteklerin ağırlıklara uygun dağıtılmasını sağlar.

Bu model, optimizasyon dersi alan yeni bir öğrenci için klasik bir **doğrusal programlama** (linear programming) örneğidir. Tüm değişkenler ve kısıtlar birinci dereceden (doğrusal) olduğu için, çözümü de doğrusaldır ve standart yöntemlerle (simplex, vb.) çözülebilir.

## 4. Kısıtlar
### a) Sunucu CPU Kapasite Kısıtı
Her sunucunun işleyebileceği istek sayısı, CPU kapasitesiyle sınırlıdır:

$$
\forall i: x_i \cdot r_{avg} \leq C_i
$$

### b) WRR Dağıtım Kısıtı
İstekler, WRR ağırlıklarına orantılı dağıtılır:

$$
\forall i: x_i = z_{max} \cdot \frac{w_i}{\sum_{j=1}^{N} w_j}
$$

### c) Bütünlük ve Pozitiflik
$$
\forall i: x_i \geq 0,\quad z_{max} \geq 0
$$

## 5. Zmax Hesaplama Formülü
Yukarıdaki kısıtlar birleştirildiğinde, her sunucu için:

$$
z_{max} \cdot \frac{w_i}{\sum_{j=1}^{N} w_j} \cdot r_{avg} \leq C_i
$$

Buradan $z_{max}$ için:

$$
z_{max} \leq \min_i \left( \frac{C_i \cdot \sum_{j=1}^{N} w_j}{w_i \cdot r_{avg}} \right)
$$

Yani, sistemin işleyebileceği maksimum istek sayısı, en kısıtlayıcı sunucuya göre belirlenir.

## 6. Sonuç

- **Amaç fonksiyonu:** $\max z_{max} = \sum_{i=1}^{N} x_i$
- **Kısıtlar:**
    - $x_i = z_{max} \cdot \frac{w_i}{\sum w_j}$
    - $x_i \cdot r_{avg} \leq C_i$
    - $x_i \geq 0$
- **Zmax formülü:**

$$
z_{max} = \min_i \left( \frac{C_i \cdot \sum_{j=1}^{N} w_j}{w_i \cdot r_{avg}} \right)
$$

---

## Amaç Fonksiyonu ve Kısıtların Doğrusallık Analizi

### 1. Amaç Fonksiyonu
$$
\max z_{max} = \sum_{i=1}^{N} x_i
$$
Bu fonksiyon **doğrusaldır**. Çünkü değişkenler birinci dereceden ve aralarında toplama işlemi vardır. Herhangi bir çarpan, üstel, logaritmik veya değişkenler arası çarpma yoktur.

### 2. Kısıtlar
- $x_i = z_{max} \cdot \frac{w_i}{\sum w_j}$: Burada $w_i$ ve $\sum w_j$ sabit parametrelerdir, değişken değildir. $x_i$ ile $z_{max}$ arasında **doğrusal** bir ilişki vardır.
- $x_i \cdot r_{avg} \leq C_i$: $r_{avg}$ ve $C_i$ sabittir, $x_i$ değişkendir. Bu da **doğrusal** bir kısıttır.
- $x_i \geq 0$, $z_{max} \geq 0$: Bunlar da doğrusal (lineer) kısıtlardır.

### 3. Zmax Formülü
$$
z_{max} = \min_i \left( \frac{C_i \cdot \sum_{j=1}^{N} w_j}{w_i \cdot r_{avg}} \right)
$$
Bu formül, her bir sunucu için doğrusal kısıtların sınır değerini bulur ve en küçük değeri seçer. $z_{max}$'ı belirleyen bu minimum fonksiyon, optimizasyon modelinin çözümünde doğrusal kısıtların birleşiminden elde edilir. Minimum alma işlemi modelin çözümünde kullanılır, ancak kısıtların kendisi doğrusal kalır.

### 4. Doğrusal Olmayan Durumlar Olabilir mi?
Eğer ağırlıklar ($w_i$), ortalama CPU ihtiyacı ($r_{avg}$) veya kapasite ($C_i$) değişken olsaydı, ya da $x_i$ ile $z_{max}$ arasında çarpma, üstel, logaritmik gibi doğrusal olmayan bir ilişki olsaydı, model doğrusal olmazdı. Ancak bu modelde tüm parametreler sabit ve değişkenler birinci dereceden olduğu için **tüm amaç fonksiyonu ve kısıtlar doğrusal**dır.

---

**Sonuç:**
- Bu optimizasyon modelinde amaç fonksiyonu ve tüm kısıtlar doğrusal (lineer) yapıdadır.
- Model, doğrusal programlama yöntemleriyle kolayca çözülebilir.
