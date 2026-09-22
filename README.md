# Remote VM Management System

Bu proje, ağdaki sanal makineleri (VM) ve sunucuları tek bir merkezden izleyip yönetmek için geliştirdiğim ajan (agent) tabanlı bir yönetim sistemi.

Sistem temelde iki parçadan oluşuyor: Merkezde her şeyi yönettiğimiz Flask tabanlı bir web paneli ve istemci makinelerde arka planda çalışan Python ajanı. Bu iki parça birbiriyle TCP soketler üzerinden doğrudan haberleşiyor.

## Neler Yapabiliyor?

* Anlık İzleme: Ajan yüklü makinelerin CPU, RAM, Disk ve ağ kullanımlarını panelden canlı olarak takip edebilirsiniz.
* Yapay Zeka Destekli Uzaktan Komut Çalıştırma: Arayüz üzerinden istediğiniz makineye kendi yazdığınız komutları gönderebileceğiniz gibi, sisteme entegre yapay zekaya anında ihtiyacınıza uygun script ürettirip hedef makinede çalıştırabilirsiniz. Sonuçları direkt merkezden görebilirsiniz (Yeni nesil SOC ve merkezi yönetim altyapısı mantığıyla kurgulandı).
* Bağımsız İstemci: Ajan kodunu PyInstaller ile tek bir `.exe` haline getirebiliyoruz. Hedef makinede Python kurulu olmasına gerek kalmadan direkt çalışıyor.
* Veritabanı Kaydı: Kullanıcı oturumları, makine bilgileri ve çalıştırılan komutların logları MySQL üzerinde güvenle tutuluyor.

## Kurulum ve Çalıştırma

Projeyi lokalinizde ayağa kaldırmak için:

1. Repoyu klonlayıp bağımlılıkları yükleyin:
   `pip install -r requirements.txt`
2. Ana dizine bir `.env` dosyası açıp MySQL veritabanı bilgilerinizi (`SECRET_KEY`, `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`) ekleyin.
3. Sunucuyu başlatın:
   `python app.py`