import tenseal as ts


def kurumsal_ckks_akisi(vektor: list[float], agirliklar: list[float]) -> float:
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
    return float(cozulen_sifreli_sonuc.decrypt()[0])
