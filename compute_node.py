import time
import tenseal as ts


class HesaplamaSunucusu:
    """Gizli anahtar olmadan yalnızca genel bağlam ve şifreli vektörle hesaplama yapar."""

    def __init__(self, genel_context_bayt: bytes):
        self.context = ts.context_from(genel_context_bayt)
        if self.context.is_private():
            raise ValueError("Güvenlik ihlali: Hesaplama sunucusuna gizli anahtarlı bağlam verilemez.")

    @property
    def gizli_anahtar_var_mi(self) -> bool:
        return self.context.is_private()

    def sifreli_dot_bayt(self, sifreli_vektor_bayt: bytes, agirliklar: list[float]) -> tuple[bytes, float]:
        t0 = time.perf_counter()
        sifreli_vektor = ts.ckks_vector_from(self.context, sifreli_vektor_bayt)
        sifreli_sonuc = sifreli_vektor.dot(agirliklar)
        bayt = sifreli_sonuc.serialize()
        sure_ms = round((time.perf_counter() - t0) * 1000, 2)
        return bayt, sure_ms
