"""Motor de simulacion: une mercado, cartera y estrategia.

``Simulador.ejecutar`` avanza el mercado sesion a sesion, pide a la
estrategia sus decisiones, las ejecuta contra la cartera y anota la curva
de valor liquidativo. El resultado es un objeto inmutable y serializable
que alimenta metricas, exportadores, CLI, GUI y concurrencia.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

from .estrategias import ContextoMercado
from .excepciones import DatosInvalidos, ErrorSimulacion
from .logging_config import obtener_logger
from .metricas import MetricasInversion, metricas_cartera

if TYPE_CHECKING:
    from .cartera import Cartera
    from .estrategias import EstrategiaInversion
    from .mercado import Mercado
    from .operacion import Operacion

log = obtener_logger(__name__)


@dataclass(frozen=True, slots=True)
class ResultadoSimulacion:
    """Resultado completo de una simulacion (inmutable y exportable)."""

    estrategia: str
    sesiones: int
    valor_inicial: float
    valor_final: float
    curva: tuple[float, ...]
    operaciones: tuple[Operacion, ...]
    metricas: MetricasInversion

    @property
    def rentabilidad_total(self) -> float:
        return self.metricas.rentabilidad_total

    @property
    def numero_operaciones(self) -> int:
        return len(self.operaciones)

    def a_dict(self) -> dict[str, Any]:
        return {
            "estrategia": self.estrategia,
            "sesiones": self.sesiones,
            "valor_inicial": self.valor_inicial,
            "valor_final": self.valor_final,
            "rentabilidad_total": self.rentabilidad_total,
            "curva": list(self.curva),
            "operaciones": [asdict(op) for op in self.operaciones],
            "metricas": self.metricas.a_dict(),
        }

    def __str__(self) -> str:
        return (
            f"[{self.estrategia}] {self.sesiones} sesiones  "
            f"valor {self.valor_inicial:.2f} -> {self.valor_final:.2f} EUR  "
            f"({self.rentabilidad_total:+.2%})  ops={self.numero_operaciones}"
        )


class Simulador:
    """Ejecuta una estrategia sobre un mercado y una cartera."""

    def __init__(
        self,
        mercado: Mercado,
        cartera: Cartera,
        estrategia: EstrategiaInversion,
        *,
        sesiones: int = 60,
        volumen: int = 100,
    ) -> None:
        if isinstance(sesiones, bool) or not isinstance(sesiones, int) or sesiones <= 0:
            raise DatosInvalidos("sesiones debe ser un entero > 0")
        if isinstance(volumen, bool) or not isinstance(volumen, int) or volumen <= 0:
            raise DatosInvalidos("volumen debe ser un entero > 0")
        self.mercado = mercado
        self.cartera = cartera
        self.estrategia = estrategia
        self.sesiones = sesiones
        self.volumen = volumen

    def ejecutar(self) -> ResultadoSimulacion:
        if not self.cartera.curva_valor:
            self.cartera.anotar_valor(mercado=self.mercado)
        ejecutadas: list[Operacion] = []
        log.info(
            "simulacion iniciada: estrategia=%s sesiones=%d cartera=%s",
            self.estrategia.nombre,
            self.sesiones,
            self.cartera.propietario,
        )

        try:
            for _ in range(self.sesiones):
                self.mercado.avanzar_sesion(self.volumen)
                contexto = ContextoMercado(
                    mercado=self.mercado,
                    cartera=self.cartera,
                    sesion=self.mercado.sesion,
                )
                for decision in self.estrategia.decidir(contexto):
                    op = self._ejecutar(decision.instrumento_id, decision.tipo, decision.cantidad)
                    if op is not None:
                        ejecutadas.append(op)
                    # El contexto debe reflejar el efectivo/posiciones ya usados.
                    contexto = ContextoMercado(
                        mercado=self.mercado,
                        cartera=self.cartera,
                        sesion=self.mercado.sesion,
                    )
                self.cartera.anotar_valor(mercado=self.mercado)
        except Exception as exc:
            log.exception("fallo durante la simulacion (estrategia=%s)", self.estrategia.nombre)
            raise ErrorSimulacion(f"fallo durante la simulacion: {exc}") from exc

        curva = self.cartera.curva_valor
        resultado = ResultadoSimulacion(
            estrategia=self.estrategia.nombre,
            sesiones=self.sesiones,
            valor_inicial=curva[0],
            valor_final=curva[-1],
            curva=curva,
            operaciones=tuple(ejecutadas),
            metricas=metricas_cartera(self.cartera, self.mercado),
        )
        log.info(
            "simulacion completada: estrategia=%s operaciones=%d rentabilidad=%+.2f%%",
            resultado.estrategia,
            resultado.numero_operaciones,
            resultado.rentabilidad_total * 100,
        )
        return resultado

    def _ejecutar(self, instrumento_id: str, tipo: str, cantidad: int) -> Operacion | None:
        precio = self.mercado.precio_de(instrumento_id)
        fecha = f"s{self.mercado.sesion:04d}"
        if tipo == "compra":
            return self.cartera.invertir(self.mercado, instrumento_id, cantidad, precio, fecha)
        return self.cartera.desinvertir(self.mercado, instrumento_id, cantidad, precio, fecha)


def simular(
    mercado: Mercado,
    cartera: Cartera,
    estrategia: EstrategiaInversion,
    *,
    sesiones: int = 60,
    volumen: int = 100,
) -> ResultadoSimulacion:
    """Atajo funcional para crear y ejecutar un ``Simulador``."""
    return Simulador(
        mercado,
        cartera,
        estrategia,
        sesiones=sesiones,
        volumen=volumen,
    ).ejecutar()


__all__ = ["ResultadoSimulacion", "Simulador", "simular"]
