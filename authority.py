import tenseal as ts


class YetkiliTaraf:
    """CKKS bağlamını yöneten, şifreleyen ve sonuçları çözen yetkili katman."""

    def __init__(
        self,
        poly_modulus_degree: int = 8192,
        coeff_mod_bit_sizes: list[int] | None = None,
        global_scale: float = 2**40,
    ):
        if coeff_mod_bit_sizes is None:
            coeff_mod_bit_sizes = [60, 40, 40, 60]

        self.context = ts.context(
            ts.SCHEME_TYPE.CKKS,
            poly_modulus_degree=poly_modulus_degree,
            coeff_mod_bit_sizes=coeff_mod_bit_sizes,
        )
        self.context.global_scale = global_scale
        self.context.generate_galois_keys()

    def genel_baglam_bayt(self) -> bytes:
        """Gizli anahtar içermeyen serileştirilmiş genel bağlamı üretir."""
        genel_context = self.context.copy()
        genel_context.make_context_public()
        return genel_context.serialize()

    def vektor_sifrele_bayt(self, vektor: list[float]) -> bytes:
        """Özellik vektörünü şifreleyip serileştirilmiş bayt olarak döndürür."""
        sifreli_vektor = ts.ckks_vector(self.context, vektor)
        return sifreli_vektor.serialize()

    def sonuc_coz_bayt(self, donen_sonuc_bayt: bytes) -> float:
        """Sunucudan dönen şifreli sonucu kendi gizli anahtarıyla çözer."""
        cozulen_sifreli_sonuc = ts.ckks_vector_from(self.context, donen_sonuc_bayt)
        return float(cozulen_sifreli_sonuc.decrypt()[0])
