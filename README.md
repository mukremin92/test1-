# Email Classifier Utility

Bu depo, e-posta içeriklerini önceden tanımlı kurallara göre sınıflandırmak ve uygun klasörlere taşımak veya silmek için küçük bir komut satırı aracı içerir.

## Kullanım

Python ile çalıştırmak için:

```bash
python email_classifier.py "gonderen@example.com" "Konu" "E-posta içeriği" --contacts arkadas@example.com
```

Komut, aşağıdaki formatta Türkçe etiketlerle JSON çıktısı üretir:

```json
{
  "category": "İş",
  "confidence": "0.85",
  "action": "move",
  "target_folder": "📁 İş",
  "summary": "Mesaj içeriğinin özeti."
}
```

## Testler

Pytest ile birim testleri çalıştırabilirsiniz:

```bash
pytest
```

## IMAP üzerinden gerçek e-postaları sınıflandırma

Kendi posta kutunuzdaki son e-postaları denemek için `imap_runner.py` komut satırı aracını kullanabilirsiniz.

### IMAP kimlik bilgilerini adım adım girme

#### Depo köküne `.env` yerleştiren hızlı kurulum (önerilen)

1. Depoyu açtığınız klasörde (`README.md` ile aynı dizin) örnek dosyayı kopyalayın:

   ```bash
   cp .env.example .env
   ```

2. Oluşan `.env` dosyasını bir metin düzenleyiciyle açın ve her satırı doldurun:

   - `IMAP_HOST`: Sağlayıcınızın IMAP sunucusu (ör. Gmail için `imap.gmail.com`).
   - `IMAP_USER`: Tam e‑posta adresiniz.
   - `IMAP_PASSWORD`: Tercihen uygulama şifreniz.

3. Dosyayı kaydedin. Bu dosya **yalnızca yerel kalmalı**; depoya veya paylaşılan ortamlara eklemeyin.

4. Doğrudan çalıştırın; komut `.env` dosyasını otomatik okuyacaktır:

   ```bash
   python imap_runner.py --limit 5
   ```

#### Alternatif: Kimlik bilgilerini ortam değişkeni olarak yazma

```bash
export IMAP_HOST="imap.ornekmail.com"
export IMAP_USER="adresiniz@ornekmail.com"
export IMAP_PASSWORD="uygulama-sifresi"
python imap_runner.py --limit 5
```

Bu yöntemde `.env` dosyası gerekmez; değerler terminal oturumunuz kapandığında sıfırlanır.

### Sınıflandırmayı çalıştırma

`imap_runner.py`, klasörünüzde `.env` varsa otomatik olarak yükler; ortam değişkenleri de çalışır.

Son 5 e-postayı sınıflandırmak için:

```bash
python imap_runner.py --limit 5
```

Komut, her e-posta için gönderen, konu, gövde ve sınıflandırma sonucunu Türkçe JSON olarak yazdırır. Kimlik bilgileriniz yalnızca yerel `.env` dosyasında veya geçici ortam değişkenlerinde tutulur; depoya eklemeyin.

Farklı bir dosya yolundaki kimlik bilgilerini kullanmak isterseniz `--env-file` argümanı ile yeni yolu verebilirsiniz:

```bash
python imap_runner.py --limit 5 --env-file /gizli/imap_credentials.env
```

Bu sayede birden fazla hesap için ayrı `.env` dosyalarını güvenli şekilde saklayabilirsiniz. Yeni dosyayı `.env.example` içeriğinden kopyalayıp doldurabilir ve istediğiniz dizinde saklayabilirsiniz.
