from django.urls import path
from .views import (AramaView, SonuclarView, GirisView, CikisView,
                    AbonelikYonetimView, AbonelikKaydetView,
                    KullaniciEkleView, OdemeGecmisiView, OdemeEkleView,
                    NotlarView, NotEkleView, NotSilView, UyelikTalepView,
                    IskontoYonetimView,
                    # Sepet & Sipariş
                    SepeteEkleView, SepetView, SepetGuncelleView, SepetSilView,
                    SiparisGonderView, SiparisTesekurView, SiparislerimView,
                    AdminSiparislerView, AdminSiparisDurumView, SepetAdetView)

urlpatterns = [
    path("",                              AramaView.as_view(),           name="arama"),
    path("sonuclar/",                     SonuclarView.as_view(),        name="sonuclar"),
    path("giris/",                        GirisView.as_view(),           name="giris"),
    path("cikis/",                        CikisView.as_view(),           name="cikis"),
    path("abonelikler/",                  AbonelikYonetimView.as_view(), name="abonelik_yonetim"),
    path("abonelikler/<int:kullanici_id>/kaydet/", AbonelikKaydetView.as_view(), name="abonelik_kaydet"),
    path("abonelikler/kullanici-ekle/",   KullaniciEkleView.as_view(),   name="kullanici_ekle"),
    path("abonelikler/odeme-ekle/",       OdemeEkleView.as_view(),       name="odeme_ekle"),
    path("odeme-gecmisim/",               OdemeGecmisiView.as_view(),    name="odeme_gecmisi"),
    # Notlar
    path("notlar/",                       NotlarView.as_view(),          name="notlar"),
    path("notlar/ekle/",                  NotEkleView.as_view(),         name="not_ekle"),
    path("notlar/<int:not_id>/sil/",      NotSilView.as_view(),          name="not_sil"),
    # Üyelik talebi
    path("uyelik-talep/",                 UyelikTalepView.as_view(),     name="uyelik_talep"),
    # İskonto yönetimi
    path("iskonto/",                      IskontoYonetimView.as_view(),  name="iskonto_yonetim"),
    # ── Sepet & Sipariş ──────────────────────────────────────────────────────
    path("sepet/",                        SepetView.as_view(),           name="sepet"),
    path("sepet/ekle/",                   SepeteEkleView.as_view(),      name="sepete_ekle"),
    path("sepet/adet/",                   SepetAdetView.as_view(),       name="sepet_adet"),
    path("sepet/<int:urun_id>/guncelle/", SepetGuncelleView.as_view(),   name="sepet_guncelle"),
    path("sepet/<int:urun_id>/sil/",      SepetSilView.as_view(),        name="sepet_sil"),
    path("siparis/gonder/",               SiparisGonderView.as_view(),   name="siparis_gonder"),
    path("siparis/<int:siparis_id>/tesekkur/", SiparisTesekurView.as_view(), name="siparis_tesekkur"),
    path("siparislerim/",                 SiparislerimView.as_view(),    name="siparislerim"),
    # ── Admin Sipariş ─────────────────────────────────────────────────────────
    path("admin-panel/siparisler/",              AdminSiparislerView.as_view(),  name="admin_siparisler"),
    path("admin-panel/siparisler/<int:siparis_id>/durum/", AdminSiparisDurumView.as_view(), name="admin_siparis_durum"),
]
