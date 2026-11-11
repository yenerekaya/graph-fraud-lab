# Projeyi anlatırken

## CV için İngilizce açıklama

**Graph Fraud Lab | Python, NetworkX, Graph Analytics**
- Built a reproducible transaction-graph investigation pipeline with explainable temporal rules for transfer rings, fan-in/fan-out patterns, and rapid fund forwarding.
- Developed a standalone interactive dashboard linking account-level signals to timestamped transaction evidence; implemented automated tests and GitHub Actions CI.
- Evaluated account-level precision and recall on labeled synthetic scenarios, explicitly measuring a legitimate merchant false positive.

## Mülakatta anlatılabilecek kararlar

- Sadece graph üzerinde cycle bulmak yeterli değil: işlemlerin zaman sırası ve tutarları da kontrol ediliyor.
- Aynı iki hesap arasındaki işlemler görselleştirmede birleştiriliyor; zaman analizi için tek tek korunuyor.
- Gerçek etiketler tespit algoritmasına verilmiyor; sadece sonuçları değerlendiren fonksiyona veriliyor.
- Meşru mağazanın yanlış işaretlenmesi kural tabanlı sistemlerin bağlam ihtiyacını gösteriyor.
- Skorlar olasılık değil. Sentetik verideki sonuçlar gerçek finansal işlemlere genellenemez.
- Bu sürüm makine öğrenmesi modeli eğitmiyor ve Neo4j kullanmıyor. Bunlar sonraki geliştirmeler olabilir.

## Küçük sonraki işler

1. Neo4j için hesap ve işlem CSV dışa aktarımı ile örnek Cypher sorguları.
2. Meşru yoğun işlemler içeren daha çeşitli senaryolar ve zamana göre ayrılmış değerlendirme.
3. Graph özellikleriyle bir anomali modeli kurup aynı veri üzerinde kurallarla karşılaştırma.

Önce kodu çalıştır, kuralları değiştir ve testleri incele. CV'ye projeyi ve katkılarını kendi açıklayabildiğin haliyle ekle.
