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


def risk_seviyesi_belirle(skor: float, esikler: dict) -> str:
    if skor < esikler["low_max"]:
        return "Düşük"
    elif skor < esikler["high_min"]:
        return "Orta"
    return "Yüksek"
