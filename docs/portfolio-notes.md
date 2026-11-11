# Projeyi anlatırken

## CV için İngilizce açıklama

**Graph Fraud Lab | Python, NetworkX, Graph Analytics**
- Built a reproducible transaction-graph investigation pipeline with explainable temporal rules for transfer rings, fan-in/fan-out patterns, and rapid fund forwarding.
- Developed an interactive dashboard with transaction filters, CSV export and chronological route tracing; linked account-level signals to timestamped transaction evidence.
- Built Neo4j-ready CSV/Cypher exports preserving individual transfers and implemented automated Python/JavaScript tests with GitHub Actions CI.
- Evaluated account-level precision and recall on labeled synthetic scenarios, explicitly measuring a legitimate merchant false positive.

## Mülakatta anlatılabilecek kararlar

- Sadece graph üzerinde cycle bulmak yeterli değil: işlemlerin zaman sırası ve tutarları da kontrol ediliyor.
- Aynı iki hesap arasındaki işlemler görselleştirmede birleştiriliyor; zaman analizi için tek tek korunuyor.
- Gerçek etiketler tespit algoritmasına verilmiyor; sadece sonuçları değerlendiren fonksiyona veriliyor.
- Meşru mağazanın yanlış işaretlenmesi kural tabanlı sistemlerin bağlam ihtiyacını gösteriyor.
- Skorlar olasılık değil. Sentetik verideki sonuçlar gerçek finansal işlemlere genellenemez.
- Bu sürüm makine öğrenmesi modeli eğitmiyor. Neo4j için CSV/Cypher aktarımı üretiyor; canlı Neo4j sorgulaması uygulamaya bağlı değil.
- Rota bulma işlemi zaman sırasını koruyor; aynı paranın taşındığını ispatladığını iddia etmiyor.

## Küçük sonraki işler

1. Neo4j aktarımını canlı veritabanında doğrulayan entegrasyon testi.
2. Meşru yoğun işlemler içeren daha çeşitli senaryolar ve zamana göre ayrılmış değerlendirme.
3. Graph özellikleriyle bir anomali modeli kurup aynı veri üzerinde kurallarla karşılaştırma.

Önce kodu çalıştır, kuralları değiştir ve testleri incele. CV'ye projeyi ve katkılarını kendi açıklayabildiğin haliyle ekle.
