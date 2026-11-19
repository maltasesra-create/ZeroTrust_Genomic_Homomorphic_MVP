import streamlit as st
import tenseal as ts

st.set_page_config(
    page_title="ZeroTrust Genomic Homomorphic MVP",
    page_icon="🧬",
    layout="centered",
)

DOMAIN_PROFILLERI = {
    "Temel GC / Uzunluk Senaryosu": {
        "aciklama": "Prototip seviyesi temel baz ve GC ağırlıklı skorlama profili.",
        "klinik_not": "Örnek modelleme içindir; klinik tanı veya tedavi kararı yerine geçmez.",
        "ornekler": {
            "Dengeli Örnek (Varsayılan)": "ATCG-TACG-GGCC-AATT",
            "Düşük GC Senaryosu": "ATAT-TATA-AATT-TTAA",
            "Yüksek GC Senaryosu": "GGGG-CCCC-GCGC-CGCG",
        },
        # Vektör sırası: [gc_sayisi, baz_uzunlugu, gc_orani, gc_at_orani, sabit_terim]
        "weights": [0.05, 0.02, 0.0, 0.0, 0.1],
        "thresholds": {"low_max": 0.5, "high_min": 0.9},
    },
    "10q23.31 PTEN Bölgesi (Örnek Domain)": {
        "aciklama": "10q23.31 PTEN bölgesine ait 120 bazlık örnek dizilim ile domain kalibrasyon simülasyonu.",
        "klinik_not": "Örnek modelleme içindir; klinik tanı veya tedavi kararı yerine geçmez.",
        "ornekler": {
            "PTEN 10q23.31 Örnek (120 bp)": (
                "ATG-ACA-GCC-ATC-ATC-AAA-GAG-ATC-GTT-AGC-AGA-AAC-AAA-AGG-AGA-"
                "TAT-CAA-GAG-GAT-GGA-TTC-GAC-TTA-GAC-TTG-ACC-TAT-ATT-TAT-CCA-"
                "AAC-ATT-ATT-GCT-ATG-GGA-TTT-CCT-GCA-GAA"
            ),
            "Düşük GC Karşılaştırma": "ATAT-TATA-AATT-TTAA-ATAT-TATA",
            "Yüksek GC Karşılaştırma": "GGGG-CCCC-GCGC-CGCG-GGGG-CCCC",
        },
        # Uzunluk şişmesini dengelemek için oran/yoğunluk ağırlıkları öne çıkarıldı
        "weights": [0.002, 0.001, 0.45, 0.05, 0.15],
        "thresholds": {"low_max": 0.45, "high_min": 0.80},
    },
}


def ozellik_vektoru_cikar(dizi: str) -> dict:
    """Genişletilebilir özellik vektörü ve oran/yoğunluk metriklerini üretir."""
    temiz_bazlar = dizi.replace("-", "")
    baz_uzunlugu = len(temiz_bazlar)

    a_sayisi = temiz_bazlar.count("A")
    t_sayisi = temiz_bazlar.count("T")
    c_sayisi = temiz_bazlar.count("C")
    g_sayisi = temiz_bazlar.count("G")

    gc_sayisi = g_sayisi + c_sayisi
    at_sayisi = a_sayisi + t_sayisi

    gc_orani = (gc_sayisi / baz_uzunlugu) if baz_uzunlugu > 0 else 0.0
    gc_at_orani = (gc_sayisi / at_sayisi) if at_sayisi > 0 else float(gc_sayisi)

    vektor = [
        float(gc_sayisi),
        float(baz_uzunlugu),
        float(gc_orani),
        float(gc_at_orani),
        1.0,
    ]

    return {
        "vektor": vektor,
        "baz_uzunlugu": baz_uzunlugu,
        "gc_sayisi": gc_sayisi,
        "at_sayisi": at_sayisi,
        "gc_orani": gc_orani,
        "gc_at_orani": gc_at_orani,
        "dagilim": {"A": a_sayisi, "T": t_sayisi, "C": c_sayisi, "G": g_sayisi},
    }


def kurumsal_ckks_akisi(vektor: list[float], agirliklar: list[float]) -> tuple[float, dict]:
    """Gizli anahtarı sunucuya vermeden CKKS şifreli iç çarpım ve çözümleme yapar."""
    # 1. Yetkili Taraf: Bağlam ve anahtarları üretir
    yetkili_context = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=[60, 40, 40, 60],
    )
    yetkili_context.global_scale = 2**40
    yetkili_context.generate_galois_keys()

    # Vektörü yetkili tarafta şifrele
    sifreli_vektor = ts.ckks_vector(yetkili_context, vektor)
    sifreli_vektor_bayt = sifreli_vektor.serialize()

    # Sunucuya gönderilecek gizli-anahtarsız genel bağlam
    genel_context = yetkili_context.copy()
    genel_context.make_context_public()
    genel_context_bayt = genel_context.serialize()

    # 2. Hesaplama Sunucusu: Gizli anahtar olmadan hesaplar
    sunucu_context = ts.context_from(genel_context_bayt)
    sunucu_vektor = ts.ckks_vector_from(sunucu_context, sifreli_vektor_bayt)
    sunucu_sifreli_sonuc = sunucu_vektor.dot(agirliklar)
    donen_sonuc_bayt = sunucu_sifreli_sonuc.serialize()

    # 3. Yetkili Taraf: Kendi gizli anahtarlı bağlamıyla sonucu çözer
    cozulen_sifreli_sonuc = ts.ckks_vector_from(yetkili_context, donen_sonuc_bayt)
    cozulmus_skor = float(cozulen_sifreli_sonuc.decrypt()[0])

    meta = {
        "sunucu_gizli_anahtar_var_mi": sunucu_context.is_private(),
        "genel_context_kb": round(len(genel_context_bayt) / 1024, 2),
        "sifreli_vektor_kb": round(len(sifreli_vektor_bayt) / 1024, 2),
        "donen_sonuc_kb": round(len(donen_sonuc_bayt) / 1024, 2),
    }
    return cozulmus_skor, meta


def risk_seviyesi_belirle(skor: float, esikler: dict) -> str:
    if skor < esikler["low_max"]:
        return "Düşük"
    elif skor < esikler["high_min"]:
        return "Orta"
    return "Yüksek"


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
            cozulmus_skor, meta = kurumsal_ckks_akisi(vektor, weights)

        risk_etiketi = risk_seviyesi_belirle(cozulmus_skor, profil["thresholds"])

        st.success("3 aşamalı kurumsal şifreli hesaplama ve sonuç çözme tamamlandı.")
        st.subheader("2. Analiz Sonuçları")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Risk Skoru", f"{cozulmus_skor:.6f}")
        with col2:
            st.metric("GC Oranı", f"%{ozellikler['gc_orani'] * 100:.1f}")
        with col3:
            st.metric("GC / AT Oranı", f"{ozellikler['gc_at_orani']:.2f}")
        with col4:
            st.metric("Risk Seviyesi", risk_etiketi)

        dag = ozellikler["dagilim"]
        st.caption(
            f"Baz Uzunluğu: {ozellikler['baz_uzunlugu']} | GC Sayısı: {ozellikler['gc_sayisi']} | "
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
            st.write("- **Güvenlik Yaklaşımı:** Sıfır Güven (Zero-Trust) ile gizli anahtar sunucuya taşınmadan uçtan uca şifreli akış.")
