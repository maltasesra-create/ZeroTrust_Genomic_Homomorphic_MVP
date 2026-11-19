import streamlit as st

from authority import YetkiliTaraf
from compute_node import HesaplamaSunucusu
from profiles import (
    DOMAIN_PROFILLERI,
    acik_skor_hesapla,
    ozellik_vektoru_cikar,
    risk_seviyesi_belirle,
)

st.set_page_config(
    page_title="ZeroTrust Genomic Homomorphic MVP",
    page_icon="🧬",
    layout="centered",
)

st.title("🧬 Zero-Trust Genomik Risk Skorlama Prototipi")
st.caption("Tam Homomorfik Şifreleme (FHE / CKKS) • Sıfır Güven (Zero-Trust) Analiz Arayüzü")
st.info(
    "🛡️ **Zero-Trust Mahremiyet Notu:** Genetik veri şifreli uzayda işlenir; "
    "gizli anahtar hesaplama sunucusuna verilmeden (`make_context_public()`) şifreli akış yürütülür."
)

st.subheader("1. Domain Profili ve Gen Dizilimi")
secili_profil_adi = st.selectbox("Domain / Profil Seç", list(DOMAIN_PROFILLERI.keys()))
profil = DOMAIN_PROFILLERI[secili_profil_adi]
st.caption(f"{profil['aciklama']} ({profil['klinik_not']})")

ornek_isimleri = list(profil["ornekler"].keys())
secili_ornek = st.selectbox("Hazır Örnek Dizilim", ornek_isimleri)
orijinal_dna = st.text_area(
    "Gen Dizilimi (A, T, C, G ve '-' karakterleri)",
    value=profil["ornekler"][secili_ornek],
    height=90,
)

if st.button("🔒 Şifrele, Şifreli Hesapla ve Sonucu Çöz", type="primary"):
    temiz_dna = orijinal_dna.strip().upper()
    gecerli_karakterler = set("ATCG-")

    if not temiz_dna or not set(temiz_dna).issubset(gecerli_karakterler):
        st.warning("Lütfen yalnızca A, T, C, G ve '-' karakterlerinden oluşan geçerli bir gen dizilimi girin.")
    else:
        with st.spinner("Yetkili bağlam hazırlanıyor, sunucuda gizli anahtarsız hesaplama ve çözümleme yapılıyor..."):
            ozellikler = ozellik_vektoru_cikar(temiz_dna)
            vektor = ozellikler["vektor"]
            weights = profil["weights"]

            acik_skor = acik_skor_hesapla(vektor, weights)

            # 1. Yetkili Taraf
            yetkili = YetkiliTaraf(
                poly_modulus_degree=8192,
                coeff_mod_bit_sizes=[60, 40, 40, 60],
                global_scale=2**40,
            )
            genel_context_bayt = yetkili.genel_baglam_bayt()
            sifreli_vektor_bayt, sifreleme_ms = yetkili.vektor_sifrele_bayt(vektor)

            # 2. Hesaplama Sunucusu
            sunucu = HesaplamaSunucusu(genel_context_bayt)
            donen_sonuc_bayt, sunucu_ms = sunucu.sifreli_dot_bayt(sifreli_vektor_bayt, weights)

            # 3. Yetkili Taraf Çözümleme
            cozulmus_skor, cozme_ms = yetkili.sonuc_coz_bayt(donen_sonuc_bayt)
            mutlak_fark = abs(acik_skor - cozulmus_skor)

            meta = {
                "sunucu_gizli_anahtar_var_mi": sunucu.gizli_anahtar_var_mi,
                "genel_context_kb": round(len(genel_context_bayt) / 1024, 2),
                "sifreli_vektor_kb": round(len(sifreli_vektor_bayt) / 1024, 2),
                "donen_sonuc_kb": round(len(donen_sonuc_bayt) / 1024, 2),
                "acik_skor": acik_skor,
                "mutlak_fark": mutlak_fark,
                "baglam_ms": yetkili.baglam_suresi_ms,
                "sifreleme_ms": sifreleme_ms,
                "sunucu_ms": sunucu_ms,
                "cozme_ms": cozme_ms,
            }

        risk_etiketi = risk_seviyesi_belirle(cozulmus_skor, profil["thresholds"])

        st.success("3 aşamalı kurumsal şifreli hesaplama ve sonuç çözme tamamlandı.")
        st.subheader("2. Analiz Sonuçları")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Risk Skoru", f"{cozulmus_skor:.6f}")
        with col2:
            st.metric("GC Oranı", f"%{ozellikler['gc_orani'] * 100:.1f}")
        with col3:
            st.metric("Tekrar Oranı", f"%{ozellikler['tekrar_orani'] * 100:.1f}")
        with col4:
            st.metric("Risk Seviyesi", risk_etiketi)

        dag = ozellikler["dagilim"]
        st.caption(
            f"Baz Uzunluğu: {ozellikler['baz_uzunlugu']} | GC Sayısı: {ozellikler['gc_sayisi']} | "
            f"Tekrar Sayısı: {ozellikler['tekrar_sayisi']} | "
            f"Nükleotid Dağılımı → A: {dag['A']} | T: {dag['T']} | C: {dag['C']} | G: {dag['G']}"
        )

        with st.expander("Teknik Özet ve Kurumsal Anahtar Ayrımı Detayları"):
            st.write(f"- **Aktif Domain Profili:** `{secili_profil_adi}`")
            st.write(f"- **Baz Uzunluğu:** `{ozellikler['baz_uzunlugu']}`")
            st.write(f"- **Özellik Vektörü:** `{[round(x, 4) for x in vektor]}`")
            st.write(f"- **Profil Katsayıları:** `{weights}`")
            st.write(f"- **Risk Eşikleri:** `{profil['thresholds']}`")
            st.write("- **CKKS Parametreleri:** `poly_modulus_degree=8192`, `scale=2^40`")
            st.write(f"- **Sunucuda Gizli Anahtar Var mı?:** `{meta['sunucu_gizli_anahtar_var_mi']}` (`make_context_public()` ile ayrıldı)")
            st.write(f"- **Genel Bağlam Boyutu:** `{meta['genel_context_kb']} KB`")
            st.write(
                f"- **Şifreli Vektör / Dönen Sonuç:** `{meta['sifreli_vektor_kb']} KB` / `{meta['donen_sonuc_kb']} KB`"
            )
            st.write(
                f"- **Açık Skor vs. CKKS Farkı:** `{meta['acik_skor']:.6f}` vs. `{cozulmus_skor:.6f}` "
                f"(Mutlak Fark: `{meta['mutlak_fark']:.8f}`)"
            )
            st.write(
                f"- **Adım Süreleri (Benchmark):** Bağlam `{meta['baglam_ms']} ms` • "
                f"Şifreleme `{meta['sifreleme_ms']} ms` • Sunucu Dot `{meta['sunucu_ms']} ms` • "
                f"Çözme `{meta['cozme_ms']} ms`"
            )
            st.write("- **Güvenlik Yaklaşımı:** Sıfır Güven (Zero-Trust) ile gizli anahtar sunucuya taşınmadan uçtan uca şifreli akış.")
