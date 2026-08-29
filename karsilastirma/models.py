from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class AramaGecmisi(models.Model):
    kullanici     = models.ForeignKey(User, on_delete=models.CASCADE, related_name="aramalar", null=True, blank=True)
    ebat          = models.CharField(max_length=30)
    marka         = models.CharField(max_length=50, blank=True)
    mevsim        = models.CharField(max_length=20, blank=True)
    sonuc_sayisi  = models.IntegerField(default=0)
    arama_zamani  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-arama_zamani"]

    def __str__(self):
        kim = self.kullanici.username if self.kullanici else "—"
        return f"{kim} | {self.ebat} {self.marka} ({self.arama_zamani:%d.%m.%Y %H:%M})"


class Abonelik(models.Model):
    """Her kullanıcıya bir abonelik kaydı. Admin panelinden yönetilir."""

    PLAN_CHOICES = [
        ("aylik",   "Aylık"),
        ("yillik",  "Yıllık"),
        ("demo",    "Demo"),
        ("deneme",  "Deneme"),
    ]

    kullanici   = models.OneToOneField(User, on_delete=models.CASCADE, related_name="abonelik")
    plan        = models.CharField(max_length=10, choices=PLAN_CHOICES, default="demo")
    baslangic   = models.DateField(default=timezone.localdate)
    bitis       = models.DateField()
    aktif       = models.BooleanField(default=True)
    not_alani   = models.TextField(blank=True, help_text="Müşteri notları")
    session_key = models.CharField(max_length=40, blank=True, default="",
                                   help_text="Aktif session key — tek oturum kontrolü için")

    class Meta:
        verbose_name        = "Abonelik"
        verbose_name_plural = "Abonelikler"
        ordering            = ["-bitis"]

    def suresi_doldu_mu(self) -> bool:
        return timezone.localdate() > self.bitis

    @property
    def erisim_var_mi(self) -> bool:
        return self.aktif and not self.suresi_doldu_mu()

    def __str__(self):
        durum = "✓" if self.erisim_var_mi else "✗"
        return f"{durum} {self.kullanici.username} — {self.bitis} ({self.plan})"


class Odeme(models.Model):
    """Kullanıcıya ait ödeme kaydı. Admin panelinden manuel olarak eklenir."""

    YONTEM_CHOICES = [
        ("nakit",       "Nakit"),
        ("havale",      "Havale / EFT"),
        ("kredi_karti", "Kredi Kartı"),
        ("diger",       "Diğer"),
    ]

    kullanici   = models.ForeignKey(User, on_delete=models.CASCADE, related_name="odemeler")
    tutar       = models.DecimalField(max_digits=10, decimal_places=2)
    tarih       = models.DateField()
    yontem      = models.CharField(max_length=20, choices=YONTEM_CHOICES, default="havale")
    aciklama    = models.TextField(blank=True, help_text="Dekont no, dönem vb.")
    olusturulma = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Ödeme"
        verbose_name_plural = "Ödemeler"
        ordering            = ["-tarih"]

    def __str__(self):
        return f"{self.kullanici.username} — {self.tutar} ₺ ({self.tarih})"


class Notlar(models.Model):
    """Kullanıcının fiyat verirken aldığı kısa notlar. 7 gün sonra otomatik silinir."""
    kullanici   = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notlar")
    ebat        = models.CharField(max_length=30, blank=True)
    marka       = models.CharField(max_length=80, blank=True)
    icerik      = models.TextField()
    olusturulma = models.DateTimeField(auto_now_add=True)
    silinme     = models.DateTimeField()

    class Meta:
        verbose_name        = "Not"
        verbose_name_plural = "Notlar"
        ordering            = ["-olusturulma"]

    def save(self, *args, **kwargs):
        if not self.pk:
            self.silinme = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def kalan_gun(self) -> int:
        delta = self.silinme - timezone.now()
        return max(0, delta.days)

    def __str__(self):
        return f"{self.kullanici.username} | {self.ebat} | {self.icerik[:40]}"


class ToptanciIskonto(models.Model):
    """Her kullanıcının her toptancı için kendi iskonto/özel fiyat notu."""
    kullanici    = models.ForeignKey(User, on_delete=models.CASCADE,
                                     related_name="iskontolar", null=True, blank=True)
    toptanci_adi = models.CharField(max_length=60,
                                    help_text="Toptancı adı (B2B_LINKLER ile eşleşmeli)")
    iskonto_metni = models.TextField(blank=True,
                                     help_text="Tooltip'te gösterilecek iskonto/not metni.")
    guncelleme   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Toptancı İskonto"
        verbose_name_plural = "Toptancı İskontolar"
        ordering            = ["toptanci_adi"]
        unique_together     = [("kullanici", "toptanci_adi")]

    def __str__(self):
        kim = self.kullanici.username if self.kullanici else "global"
        return f"{kim} / {self.toptanci_adi}: {self.iskonto_metni[:40]}"


# ─────────────────────────────────────────────────────────────────────────────
# SİPARİŞ SİSTEMİ
# ─────────────────────────────────────────────────────────────────────────────

class SepetUrun(models.Model):
    """
    Kullanıcının aktif sepetindeki her bir ürün satırı.
    Her kullanıcının sepetinde aynı (toptanci+urun_adi+ebat) sadece bir kez olabilir;
    miktar arttırılabilir.
    """
    kullanici   = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sepet")
    toptanci    = models.CharField(max_length=80)
    urun_adi    = models.CharField(max_length=255)
    marka       = models.CharField(max_length=100, blank=True)
    ebat        = models.CharField(max_length=30)
    mevsim      = models.CharField(max_length=20, blank=True)
    dot         = models.CharField(max_length=20, blank=True)
    fiyat       = models.DecimalField(max_digits=10, decimal_places=2)
    miktar      = models.PositiveSmallIntegerField(default=1)
    eklenme     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Sepet Ürünü"
        verbose_name_plural = "Sepet Ürünleri"
        ordering            = ["-eklenme"]

    def toplam_fiyat(self):
        return self.fiyat * self.miktar

    def __str__(self):
        return f"{self.kullanici.username} | {self.marka} {self.ebat} @ {self.toptanci} x{self.miktar}"


class Siparis(models.Model):
    """
    Kullanıcının "Sipariş Gönder" butonuna bastığında oluşan sipariş kaydı.
    Admin bu kaydı görerek temin işlemini yapar.
    """
    DURUM_CHOICES = [
        ("bekliyor",    "Bekliyor"),
        ("hazirlaniyor","Hazırlanıyor"),
        ("tamamlandi",  "Tamamlandı"),
        ("iptal",       "İptal"),
    ]

    kullanici   = models.ForeignKey(User, on_delete=models.CASCADE, related_name="siparisler")
    durum       = models.CharField(max_length=20, choices=DURUM_CHOICES, default="bekliyor")
    not_alani   = models.TextField(blank=True, help_text="Kullanıcı notu")
    admin_notu  = models.TextField(blank=True, help_text="Admin iç notu")
    olusturulma = models.DateTimeField(auto_now_add=True)
    guncelleme  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Sipariş"
        verbose_name_plural = "Siparişler"
        ordering            = ["-olusturulma"]

    def toplam_tutar(self):
        return sum(u.toplam_fiyat() for u in self.urunler.all())

    def toplam_tutar_ham(self):
        return sum(u.toplam_fiyat_ham() for u in self.urunler.all())

    def toplam_kar(self):
        return sum(u.toplam_kar() for u in self.urunler.all())

    def urun_sayisi(self):
        return sum(u.miktar for u in self.urunler.all())

    def __str__(self):
        return f"#{self.pk} — {self.kullanici.username} ({self.get_durum_display()}) {self.olusturulma:%d.%m.%Y %H:%M}"


class SiparisUrun(models.Model):
    """
    Siparişe bağlı her bir ürün satırı (snapshot — sipariş anındaki fiyat korunur).
    fiyat      : kullanıcıya gösterilen fiyat (%10 zam dahil)
    fiyat_ham  : toptancıdan gelen gerçek alış fiyatı (admin karşılaştırması için)
    """
    siparis     = models.ForeignKey(Siparis, on_delete=models.CASCADE, related_name="urunler")
    toptanci    = models.CharField(max_length=80)
    urun_adi    = models.CharField(max_length=255)
    marka       = models.CharField(max_length=100, blank=True)
    ebat        = models.CharField(max_length=30)
    mevsim      = models.CharField(max_length=20, blank=True)
    dot         = models.CharField(max_length=20, blank=True)
    fiyat       = models.DecimalField(max_digits=10, decimal_places=2,
                                      help_text="Kullanıcıya gösterilen fiyat (%10 zam dahil)")
    fiyat_ham   = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                      help_text="Toptancı ham alış fiyatı")
    miktar      = models.PositiveSmallIntegerField(default=1)

    class Meta:
        verbose_name        = "Sipariş Ürünü"
        verbose_name_plural = "Sipariş Ürünleri"

    def toplam_fiyat(self):
        return self.fiyat * self.miktar

    def toplam_fiyat_ham(self):
        return self.fiyat_ham * self.miktar

    def kar(self):
        """Birim başına kâr (zam - ham)."""
        return self.fiyat - self.fiyat_ham

    def toplam_kar(self):
        return self.kar() * self.miktar

    def __str__(self):
        return f"{self.marka} {self.ebat} @ {self.toptanci} x{self.miktar}"
