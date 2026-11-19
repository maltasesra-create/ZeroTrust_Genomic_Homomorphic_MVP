import time
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

        t0 = time.perf_counter()
        self.context = ts.context(
            ts.SCHEME_TYPE.CKKS,
            poly_modulus_degree=poly_modulus_degree,
            coeff_mod_bit_sizes=coeff_mod_bit_sizes,
        )
        self.context.global_scale = global_scale
        self.context.generate_galois_keys()
        self.baglam_suresi_ms = round((time.perf_counter() - t0) * 1000, 2)

    def genel_baglam_bayt(self) -> bytes:
        """Gizli anahtar içermeyen serileştirilmiş genel bağlamı üretir."""
        genel_context = self.context.copy()
        genel_context.make_context_public()
        return genel_context.serialize()

    def vektor_sifrele_bayt(self, vektor: list[float]) -> tuple[bytes, float]:
        """Özellik vektörünü şifreleyip serileştirilmiş bayt ve süreyi (ms) döndürür."""
        t0 = time.perf_counter()
        sifreli_vektor = ts.ckks_vector(self.context, vektor)
        bayt = sifreli_vektor.serialize()
        sure_ms = round((time.perf_counter() - t0) * 1000, 2)
        return bayt, sure_ms

    def sonuc_coz_bayt(self, donen_sonuc_bayt: bytes) -> tuple[float, float]:
        """Sunucudan dönen şifreli sonucu çözer ve süreyi (ms) döndürür."""
        t0 = time.perf_counter()
        cozulen_sifreli_sonuc = ts.ckks_vector_from(self.context, donen_sonuc_bayt)
        skor = float(cozulen_sifreli_sonuc.decrypt()[0])
        sure_ms = round((time.perf_counter() - t0) * 1000, 2)
        return skor, sure_ms
