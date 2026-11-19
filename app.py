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
        "ornek_dizi": "ATCG-TACG-GG
