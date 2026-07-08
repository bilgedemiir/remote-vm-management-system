# Proje Geliştirme Planı

## Proje Konusu

Proje aynı ağ üzerinde çalışan sanal makineler arasında istemci-sunucu mimarisi kullanılarak uzaktan komut gönderme, dosya transferi ve temel sistem yönetimi işlemlerini gerçekleştirebilen bir yönetim sistemi geliştirmeyi amaçlamaktadır.

## Projenin Amacı

Bu projede aynı ağ üzerinde çalışan sanal makineler arasında haberleşebilen bir uzaktan yönetim sistemi geliştirmeyi hedefliyorum. Yönetim paneli üzerinden aynı ağdaki istemcilere komut gönderilebilmesi, dosya transferi yapılabilmesi ve temel sistem bilgilerinin görüntülenebilmesi amaçlanmaktadır. Proje boyunca istemci-sunucu mimarisinin çalışma mantığını daha iyi anlamayı ve bu tür sistemlerin güvenlik açısından dikkat edilmesi gereken yönlerini incelemeyi planlıyorum.

## Geliştirme Süreci

### 1. Hafta (29 Haziran - 3 Temmuz)

Projenin temel yapısını oluşturmayı planlıyorum. Bu kısımda Flask uygulamasını kuracak, proje mimarisini oluşturacak, MySQL veritabanı bağlantısını gerçekleştirecek, kullanıcı giriş sistemini geliştirecek ve yönetim panelinin temel kısımlarını hazırlayacağım.

### 2. Hafta (6 Temmuz - 10 Temmuz)

İstemci ve sunucu arasındaki haberleşmeyi socket yapısını kullanarak geliştireceğim. Agent uygulamasını geliştirecek ve istemcilerin sunucuya bağlanmasını sağlayacağım.

### 3. Hafta (13 Temmuz - 17 Temmuz)

Yönetim paneli üzerinden istemcilere uzaktan komut gönderme sistemi geliştireceğim. Burada gönderilen komutların istemci tarafından çalıştırılması ve sonuçlarının sunucuya iletilmesi sağlanacak.

### 4. Hafta (20 Temmuz - 24 Temmuz)

Sunucu ile istemci arasında dosya transferi işlemlerini geliştireceğim. Dosya gönderme ve alma işlemleri ek olarak transfer kayıtlarının tutulması da olacaktır.

### 5. Hafta (27 Temmuz - 31 Temmuz)

İstemcilerden temel sistem bilgilerini alarak, loglama sistemini geliştirecek ve yönetim panelinde gerekli arayüz düzenlemelerini yapacağım. Ayrıca temel güvenlik iyileştirmeleride gerçekleştireceğim.

### 6. Hafta (3 Ağustos - 7 Ağustos)

Geliştirilen özellikler test edilecek, gerekli düzenlemeler yapılacak ve proje dokümantasyonunun tamamlayacağım.

### Son Gün (10 Ağustos)

Son kontrolleri yaparak GitHub düzenlemeleri tamamlanacak ve proje teslim edeceğim.