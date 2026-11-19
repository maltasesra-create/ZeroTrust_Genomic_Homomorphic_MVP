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

DOMAIN_PROFILLERI = {
    "PTEN Tümör Baskılayıcı (Örnek Domain)": {
        "aciklama": (
            "10q23.31 PTEN bölgesine ait 120 bazlık örnek dizilim ile domain kalibrasyon simülasyonu "
            "(örnek modelleme içindir; klinik tanı yerine geçmez)."
        ),
        "ornek_dizi": (
            "ATG-ACA-GCC-ATC-ATC-AAA-GAG-ATC-GTT-AGC-AGA-AAC-AAA-AGG-AGA-"
            "TAT-CAA-GAG-GAT-GGA-TTC-GAC-TTA-GAC-TTG-ACC-TAT-ATT-TAT-CCA-"
            "AAC-ATT-ATT-GCT-ATG-GGA-TTT-CCT-GCA-GAA"
        ),
        "katsayilar": [0.06, 0.025, 0.1],
        "esik_dusuk": 2.5,
        "esik_yuksek": 4.5,
    },
    "Yüksek GC / Regülatif Bölge (Örnek Domain)": {
        "aciklama": "GC yoğunluğu yüksek bölgelerin özel katsayılarla şifreli puanlanması.",
        "ornek_dizi": "GGGG-CCCC-GCGC-CGCG",
        "katsayilar": [0.07, 0.02, 0.1],
        "esik_dusuk": 1.0,
        "esik_yuksek": 1.6,
    },
    "Dengeli Referans Profili (Örnek Domain)": {
        "aciklama": "Dengeli A/T/C/G dağılımına sahip kontrol/referans domain profili.",
        "ornek_dizi": "ATCG-TACG-GGCC-AATT",
        "katsayilar": [0.04, 0.02, 0.1],
        "esik_dusuk": 0.5,
        "esik_yuksek": 1.1,
    },
}


def ckks_skor_hesapla(
    dna_dizisi: str,
    katsayilar: list[float] | None = None,
    esik_dusuk: float = 0.5,
    esik_yuksek: float = 0.9,
):
    aktif_katsayilar = katsayilar if katsayilar is not None else RISK_KATSAYILARI

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
    sifreli_skor = sifreli_vektor.dot(aktif_katsayilar)
    cozulmus_skor = float(sifreli_skor.decrypt()[0])

    gc_orani = (gc_sayisi / baz_uzunlugu) * 100 if baz_uzunlugu > 0 else 0.0
    gc_at_orani = (gc_sayisi / at_sayisi) if at_sayisi > 0 else gc_sayisi

    if cozulmus_skor < esik_dusuk:
        risk_etiketi = "Düşük"
    elif cozulmus_skor < esik_yuksek:
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
        "katsayilar": aktif_katsayilar,
        "baz_dagilimi": {
            "A": a_sayisi,
            "T": t_sayisi,
            "C": c_sayisi,
            "G": g_sayisi,
            "-": tire_sayisi,
        },
    }


def dizi_gecerli_mi(dizi: str) -> bool:
    temiz = dizi.strip().upper()
    if not temiz or not set(temiz).issubset(set("ATCG-")):
        return False
    return len(temiz.replace("-", "")) > 0


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
    if not dizi_gecerli_mi(orijinal_dna):
        st.warning("Lütfen yalnızca A, T, C, G ve '-' karakterlerinden oluşan ve en az 1 baz içeren geçerli bir dizilim girin.")
    else:
        with st.spinner("CKKS şifreli hesaplama yapılıyor..."):
            sonuc = ckks_skor_hesapla(orijinal_dna)

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
            st.write(f"- **Risk Katsayıları:** `{sonuc['katsayilar']}`")
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

st.markdown("---")
st.subheader("3. Domain / Hastalık Profili Simülasyonu (MVP)")
st.caption(
    "Seçilen domain profilinin katsayı ve eşiklerine göre şifreli skorlama simülasyonu "
    "(örnek modelleme içindir; klinik tanı veya tedavi kararı yerine geçmez)."
)

secili_domain = st.selectbox(
    "Domain / Profil Seç",
    list(DOMAIN_PROFILLERI.keys()),
    key="domain_profil_secici",
)
domain_detay = DOMAIN_PROFILLERI[secili_domain]
st.caption(f"ℹ️ {domain_detay['aciklama']}")

domain_dizi = st.text_area(
    "Domain Dizilimi (A, T, C, G ve '-' karakterleri)",
    value=domain_detay["ornek_dizi"],
    height=90,
    key=f"domain_dizi_{secili_domain}",
)

if st.button("🧬 Seçili Domain Profili ile Şifreli Skorla", use_container_width=True):
    if not dizi_gecerli_mi(domain_dizi):
        st.warning("Lütfen yalnızca A, T, C, G ve '-' karakterlerinden oluşan ve en az 1 baz içeren geçerli bir dizilim girin.")
    else:
        with st.spinner("Seçili domain katsayılarıyla CKKS hesaplaması yapılıyor..."):
            d_sonuc = ckks_skor_hesapla(
                domain_dizi,
                katsayilar=domain_detay["katsayilar"],
                esik_dusuk=domain_detay["esik_dusuk"],
                esik_yuksek=domain_detay["esik_yuksek"],
            )

        d1, d2, d3 = st.columns(3)
        d1.metric("Domain Skoru", f"{d_sonuc['skor']:.6f}")
        d2.metric("Simülasyon Seviyesi", d_sonuc["risk"])
        d3.metric("GC Oranı", f"%{d_sonuc['gc_orani']:.1f}")

        st.caption(
            f"Domain Katsayıları: `{domain_detay['katsayilar']}` | "
            f"Eşikler: Düşük < {domain_detay['esik_dusuk']} | "
            f"Orta < {domain_detay['esik_yuksek']} | "
            f"Yüksek ≥ {domain_detay['esik_yuksek']}"
        )
