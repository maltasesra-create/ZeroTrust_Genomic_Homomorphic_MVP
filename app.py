import streamlit as st
import tenseal as ts

st.set_page_config(
    page_title="ZeroTrust Genomic Homomorphic MVP",
    page_icon="🧬",
    layout="centered",
)

SENARYOLAR = {
    "Düşük GC Senaryosu": {
        "dizi": "ATAT-TATA-AATT-TTAA",
        "aciklama": "GC oranı düşük dizilim profili; düşük risk skoru ve temel baz dengesi örneği.",
    },
    "Dengeli Örnek (Varsayılan)": {
        "dizi": "ATCG-TACG-GGCC-AATT",
        "aciklama": "A, T, C ve G bazlarının dengeli dağıldığı orta düzey referans profili.",
    },
    "Yüksek GC Senaryosu": {
        "dizi": "GGGG-CCCC-GCGC-CGCG",
        "aciklama": "GC oranı yüksek dizilim profili; yüksek risk skoru üreten yoğun GC örneği.",
    },
}

st.title("🧬 Zero-Trust Genomik Risk Skorlama Prototipi")
st.caption("Tam Homomorfik Şifreleme (FHE / CKKS) • Sıfır Güven (Zero-Trust) Analiz Arayüzü")

k1, k2, k3 = st.columns(3)
with k1:
    st.metric("Şifreleme Şeması", "CKKS (FHE)")
with k2:
    st.metric("Güven Modeli", "Zero-Trust")
with k3:
    st.metric("Veri Modu", "Örnek Prototip")

st.info(
    "🛡️ **Zero-Trust Mahremiyet Notu:** Genetik özellik vektörü şifreli uzayda işlenir; "
    "skorlama hesaplaması açık metin yerine CKKS şifreli bağlam üzerinden yürütülür."
)

st.markdown("---")
st.subheader("1. Senaryo ve Gen Dizilimi")

if "aktif_senaryo" not in st.session_state:
    st.session_state.aktif_senaryo = "Dengeli Örnek (Varsayılan)"
if "dna_girdisi" not in st.session_state:
    st.session_state.dna_girdisi = SENARYOLAR[st.session_state.aktif_senaryo]["dizi"]


def senaryo_degisti():
    secim = st.session_state.secici_kutusu
    st.session_state.aktif_senaryo = secim
    st.session_state.dna_girdisi = SENARYOLAR[secim]["dizi"]


st.selectbox(
    "Hazır Senaryo Seç",
    list(SENARYOLAR.keys()),
    index=list(SENARYOLAR.keys()).index(st.session_state.aktif_senaryo),
    key="secici_kutusu",
    on_change=senaryo_degisti,
)

st.caption(f"ℹ️ {SENARYOLAR[st.session_state.aktif_senaryo]['aciklama']}")

orijinal_dna = st.text_input(
    "Gen Dizilimi (A, T, C, G ve '-' karakterleri)",
    key="dna_girdisi",
    help="Hazır senaryo seçebilir veya kendi örnek diziliminizi yazabilirsiniz.",
)

# [GC sayısı ağırlığı, toplam baz uzunluğu ağırlığı, sabit terim]
risk_katsayilari = [0.05, 0.02, 0.1]

calistir = st.button("🔒 Şifrele, Şifreli Hesapla ve Sonucu Çöz", type="primary", use_container_width=True)

if calistir:
    temiz_dna = orijinal_dna.strip().upper()
    gecerli_karakterler = set("ATCG-")

    if not temiz_dna or not set(temiz_dna).issubset(gecerli_karakterler):
        st.warning("Lütfen yalnızca A, T, C, G ve '-' karakterlerinden oluşan geçerli bir gen dizilimi girin.")
    else:
        baz_uzunlugu = float(len(temiz_dna.replace("-", "")))
        if baz_uzunlugu == 0:
            st.warning("En az 1 adet nükleotid bazı (A, T, C veya G) girmelisiniz.")
        else:
            with st.spinner("CKKS bağlamı kuruluyor, vektör şifreleniyor ve homomorfik iç çarpım yapılıyor..."):
                context = ts.context(
                    ts.SCHEME_TYPE.CKKS,
                    poly_modulus_degree=8192,
                    coeff_mod_bit_sizes=[60, 40, 40, 60],
                )
                context.global_scale = 2**40
                context.generate_galois_keys()

                gc_sayisi = float(temiz_dna.count("G") + temiz_dna.count("C"))
                vektor = [gc_sayisi, baz_uzunlugu, 1.0]

                # İstemci tarafı şifreleme
                sifreli_vektor = ts.ckks_vector(context, vektor)

                # Şifreli uzayda iç çarpım (dot product)
                sifreli_skor = sifreli_vektor.dot(risk_katsayilari)

                # Yetkili çözümleme
                cozulmus_skor = float(sifreli_skor.decrypt()[0])

            gc_orani = (gc_sayisi / baz_uzunlugu) * 100

            if cozulmus_skor < 0.5:
                risk_etiketi = "Düşük"
            elif cozulmus_skor < 0.9:
                risk_etiketi = "Orta"
            else:
                risk_etiketi = "Yüksek"

            st.markdown("---")
            st.success("Şifreli hesaplama ve sonuç çözme işlemi tamamlandı.")
            st.subheader("2. Analiz Sonuçları")

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Risk Skoru", f"{cozulmus_skor:.6f}")
            with c2:
                st.metric("GC Baz Sayısı", int(gc_sayisi))
            with c3:
                st.metric("GC Oranı", f"%{gc_orani:.1f}")
            with c4:
                st.metric("Risk Seviyesi", risk_etiketi)

            with st.expander("Teknik Özet ve Güvenlik Detayları"):
                st.write(f"- **İşlenen Dizi:** `{temiz_dna}`")
                st.write(f"- **Baz Uzunluğu:** `{int(baz_uzunlugu)}`")
                st.write(f"- **Özellik Vektörü:** `{vektor}`")
                st.write(f"- **Risk Katsayıları:** `{risk_katsayilari}`")
                st.write("- **Mimari:** CKKS yaklaşık homomorfik aritmetik ile şifreli vektör iç çarpımı.")
                st.write("- **Güvenlik Yaklaşımı:** Sıfır güven (Zero-Trust) ilkesiyle uçtan uca şifreli akış.")
                st.write("- **Prototip Notu:** Sunum ve doğrulama amaçlı örnek dizilimlerle çalışan erken aşama MVP.")
