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
        "aciklama": "Düşük GC oranına sahip sabit referans dizilimi.",
    },
    "Dengeli Örnek (Varsayılan)": {
        "dizi": "ATCG-TACG-GGCC-AATT",
        "aciklama": "A, T, C ve G bazlarının dengeli olduğu sabit referans dizilimi.",
    },
    "Yüksek GC Senaryosu": {
        "dizi": "GGGG-CCCC-GCGC-CGCG",
        "aciklama": "Yüksek GC oranına sahip sabit referans dizilimi.",
    },
}

# [GC sayısı ağırlığı, toplam baz uzunluğu ağırlığı, sabit terim]
RISK_KATSAYILARI = [0.05, 0.02, 0.1]


def ckks_skor_hesapla(dna_dizisi: str):
    temiz_dna = dna_dizisi.strip().upper()
    sadece_baz = temiz_dna.replace("-", "")
    baz_uzunlugu = float(len(sadece_baz))

    a_sayisi = temiz_dna.count("A")
    t_sayisi = temiz_dna.count("T")
    c_sayisi = temiz_dna.count("C")
    g_sayisi = temiz_dna.count("G")
    tire_sayisi = temiz_dna.count("-")

    gc_sayisi = float(g_sayisi + c_sayisi)
    at_sayisi = float(a_sayisi + t_sayisi)
    vektor = [gc_sayisi, baz_uzunlugu, 1.0]

    context = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=[60, 40, 40, 60],
    )
    context.global_scale = 2**40
    context.generate_galois_keys()

    sifreli_vektor = ts.ckks_vector(context, vektor)
    sifreli_skor = sifreli_vektor.dot(RISK_KATSAYILARI)
    cozulmus_skor = float(sifreli_skor.decrypt()[0])

    gc_orani = (gc_sayisi / baz_uzunlugu) * 100 if baz_uzunlugu > 0 else 0.0
    gc_at_orani = (gc_sayisi / at_sayisi) if at_sayisi > 0 else gc_sayisi

    if cozulmus_skor < 0.5:
        risk_etiketi = "Düşük"
    elif cozulmus_skor < 0.9:
        risk_etiketi = "Orta"
    else:
        risk_etiketi = "Yüksek"

    return {
        "dizi": temiz_dna,
        "baz_uzunlugu": int(baz_uzunlugu),
        "gc_sayisi": int(gc_sayisi),
        "at_sayisi": int(at_sayisi),
        "gc_orani": gc_orani,
        "gc_at_orani": gc_at_orani,
        "skor": cozulmus_skor,
        "risk": risk_etiketi,
        "vektor": vektor,
        "baz_dagilimi": {
            "A": a_sayisi,
            "T": t_sayisi,
            "C": c_sayisi,
            "G": g_sayisi,
            "-": tire_sayisi,
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
    st.metric("Veri Modu", "Sabit / Özel Giriş")

st.info(
    "🛡️ **Zero-Trust Mahremiyet Notu:** Genetik özellik vektörü şifreli uzayda işlenir; "
    "skorlama hesaplaması açık metin yerine CKKS şifreli bağlam üzerinden yürütülür."
)

st.markdown("---")
st.subheader("1. Senaryo ve Gen Dizilimi")

secili_senaryo = st.selectbox(
    "Hazır Senaryo Seç",
    list(SENARYOLAR.keys()),
    index=1,
)
st.caption(f"ℹ️ {SENARYOLAR[secili_senaryo]['aciklama']}")

orijinal_dna = st.text_input(
    "Gen Dizilimi (A, T, C, G ve '-' karakterleri)",
    value=SENARYOLAR[secili_senaryo]["dizi"],
    key=f"dna_input_{secili_senaryo}",
)

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    tekli_calistir = st.button("🔒 Şifrele, Hesapla ve Çöz", type="primary", use_container_width=True)
with col_btn2:
    kiyasla_calistir = st.button("📊 3 Senaryoyu Yan Yana Kıyasla", use_container_width=True)

if tekli_calistir:
    temiz_dna = orijinal_dna.strip().upper()
    gecerli_karakterler = set("ATCG-")
    if not temiz_dna or not set(temiz_dna).issubset(gecerli_karakterler):
        st.warning("Lütfen yalnızca A, T, C, G ve '-' karakterlerinden oluşan geçerli bir gen dizilimi girin.")
    elif len(temiz_dna.replace("-", "")) == 0:
        st.warning("En az 1 adet nükleotid bazı (A, T, C veya G) girmelisiniz.")
    else:
        with st.spinner("CKKS şifreli hesaplama yapılıyor..."):
            sonuc = ckks_skor_hesapla(temiz_dna)

        st.markdown("---")
        st.success("Tekli şifreli analiz tamamlandı.")
        st.subheader("2. Analiz Sonuçları")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Risk Skoru", f"{sonuc['skor']:.6f}")
        with c2:
            st.metric("GC Oranı", f"%{sonuc['gc_orani']:.1f}")
        with c3:
            st.metric("GC / AT Oranı", f"{sonuc['gc_at_orani']:.2f}")
        with c4:
            st.metric("Risk Seviyesi", sonuc["risk"])

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("GC Baz Sayısı", sonuc["gc_sayisi"])
        with m2:
            st.metric("AT Baz Sayısı", sonuc["at_sayisi"])
        with m3:
            st.metric("Baz Uzunluğu", sonuc["baz_uzunlugu"])

        st.caption(
            f"Nükleotid Dağılımı → A: {sonuc['baz_dagilimi']['A']} | "
            f"T: {sonuc['baz_dagilimi']['T']} | "
            f"C: {sonuc['baz_dagilimi']['C']} | "
            f"G: {sonuc['baz_dagilimi']['G']} | "
            f"Ayraç (-): {sonuc['baz_dagilimi']['-']}"
        )

        with st.expander("Teknik Özet ve Güvenlik Detayları"):
            st.write(f"- **İşlenen Dizi:** `{sonuc['dizi']}`")
            st.write(f"- **Özellik Vektörü:** `{sonuc['vektor']}`")
            st.write(f"- **Risk Katsayıları:** `{RISK_KATSAYILARI}`")
            st.write("- **CKKS Parametreleri:** `poly_modulus_degree=8192`, `scale=2^40`")
            st.write("- **Güvenlik Yaklaşımı:** Sıfır güven (Zero-Trust) ilkesiyle uçtan uca şifreli akış.")

if kiyasla_calistir:
    st.markdown("---")
    st.subheader("3 Senaryo Yan Yana Kıyaslama (Sabit Referans Dizilimleri)")
    st.caption("Üç temel profil sabit dizilimlerle ayrı ayrı şifrelenip skorlanarak tutarlılık gösterilir.")

    with st.spinner("Sabit senaryolar şifreli uzayda hesaplanıyor..."):
        kiyas_kartlari = []
        tablo_satirlari = []
        for ad, icerik in SENARYOLAR.items():
            res = ckks_skor_hesapla(icerik["dizi"])
            kiyas_kartlari.append((ad, res))
            dag = res["baz_dagilimi"]
            tablo_satirlari.append({
                "Senaryo": ad,
                "Sabit Dizilim": res["dizi"],
                "Uzunluk": res["baz_uzunlugu"],
                "GC Oranı": f"%{res['gc_orani']:.1f}",
                "GC / AT": f"{res['gc_at_orani']:.2f}",
                "A/T/C/G": f"{dag['A']}/{dag['T']}/{dag['C']}/{dag['G']}",
                "Risk Skoru": round(res["skor"], 6),
                "Risk Seviyesi": res["risk"],
            })

    cols = st.columns(3)
    for idx, (ad, res) in enumerate(kiyas_kartlari):
        with cols[idx]:
            st.markdown(f"**{ad}**")
            st.caption(f"`{res['dizi']}`")
            st.metric("Risk Skoru", f"{res['skor']:.6f}")
            st.write(f"GC Oranı: **%{res['gc_orani']:.1f}**")
            st.write(f"GC / AT: **{res['gc_at_orani']:.2f}**")
            st.write(f"Risk: **{res['risk']}**")

    st.dataframe(tablo_satirlari, use_container_width=True, hide_index=True)
