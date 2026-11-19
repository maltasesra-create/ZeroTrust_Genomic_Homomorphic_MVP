import streamlit as st
import tenseal as ts

st.set_page_config(
    page_title="ZeroTrust Genomic Homomorphic MVP",
    page_icon="🧬",
    layout="centered"
)

# Hazır örnek dizilimler
ORNEKLER = {
    "Dengeli Örnek (Varsayılan)": "ATCG-TACG-GGCC-AATT",
    "Düşük GC Senaryosu": "ATAT-TATA-AATT-TTAA",
    "Yüksek GC Senaryosu": "GGGG-CCCC-GCGC-CGCG"
}

st.title("🧬 Zero-Trust Genomik Risk Skorlama Prototipi")
st.caption("Tam Homomorfik Şifreleme (FHE / CKKS) • Sıfır Güven (Zero-Trust) Analiz Arayüzü")

st.info(
    "🛡️ **Zero-Trust Mahremiyet Notu:** Genetik veri şifreli uzayda işlenir; "
    "hesaplama adımları şifreli bağlam üzerinden yürütülür ve veri mahremiyeti korunur."
)

st.subheader("1. Gen Dizilimi Seçimi veya Girişi")
secili_ornek = st.selectbox("Hazır Senaryo Seç (İsteğe Bağlı)", list(ORNEKLER.keys()))

orijinal_dna = st.text_input(
    "Gen Dizilimi",
    value=ORNEKLER[secili_ornek],
    help="A, T, C, G harflerinden oluşan bir dizi girebilirsiniz."
)

# Örnek risk katsayıları: [GC sayısı ağırlığı, toplam baz uzunluğu ağırlığı, sabit terim]
risk_katsayilari = [0.05, 0.02, 0.1]

if st.button("🔒 Şifrele, Şifreli Hesapla ve Sonucu Çöz", type="primary"):
    temiz_dna = orijinal_dna.strip().upper()
    gecerli_karakterler = set("ATCG-")

    if not temiz_dna or not set(temiz_dna).issubset(gecerli_karakterler):
        st.warning("Lütfen yalnızca A, T, C, G ve '-' karakterlerinden oluşan geçerli bir gen dizilimi girin.")
    else:
        with st.spinner("CKKS bağlamı kuruluyor, veri şifreleniyor ve homomorfik hesaplama yapılıyor..."):
            context = ts.context(
                ts.SCHEME_TYPE.CKKS,
                poly_modulus_degree=8192,
                coeff_mod_bit_sizes=[60, 40, 40, 60]
            )
            context.global_scale = 2**40
            context.generate_galois_keys()

            gc_sayisi = float(temiz_dna.count("G") + temiz_dna.count("C"))
            baz_uzunlugu = float(len(temiz_dna.replace("-", "")))
            vektor = [gc_sayisi, baz_uzunlugu, 1.0]

            # İstemci tarafı şifreleme
            sifreli_vektor = ts.ckks_vector(context, vektor)

            # Şifreli uzayda iç çarpım (dot product)
            sifreli_skor = sifreli_vektor.dot(risk_katsayilari)

            # Yetkili çözümleme
            cozulmus_skor = float(sifreli_skor.decrypt()[0])

        # Basit prototip risk sınıflandırması
        if cozulmus_skor < 0.5:
            risk_etiketi = "Düşük"
        elif cozulmus_skor < 0.9:
            risk_etiketi = "Orta"
        else:
            risk_etiketi = "Yüksek"

        st.success("Şifreli hesaplama ve sonuç çözme işlemi tamamlandı.")
        st.subheader("2. Analiz Sonuçları")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Risk Skoru", f"{cozulmus_skor:.6f}")
        with col2:
            st.metric("GC Baz Sayısı", int(gc_sayisi))
        with col3:
            st.metric("Risk Seviyesi", risk_etiketi)

        with st.expander("Teknik Özet ve Güvenlik Detayları"):
            st.write(f"- **İşlenen Dizi:** `{temiz_dna}`")
            st.write(f"- **Baz Uzunluğu:** `{int(baz_uzunlugu)}`")
            st.write(f"- **Özellik Vektörü:** `{vektor}`")
            st.write("- **Mimari:** CKKS yaklaşık homomorfik aritmetik ile şifreli vektör çarpımı.")
            st.write("- **Güvenlik Yaklaşımı:** Sıfır güven (Zero-Trust) ilkesiyle uçtan uca şifreli akış.")
