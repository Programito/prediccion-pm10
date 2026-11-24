"""Render the descriptive 2024 error audit using notebook plotting dependencies."""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent


def main():
    folder = ROOT / "output/pm10_error_analysis"
    groups = pd.read_csv(folder / "grupos.csv")
    monthly = groups.loc[groups.station.eq("todas") & groups.level.eq("todos") & groups.month.gt(0)]
    sensitivity = pd.read_csv(folder / "sensibilidad_fechas.csv")
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 10})
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.4))
    axes[0].bar(monthly.month, monthly.delta_mae,
                color=["#28715c" if value < 0 else "#a34c20" for value in monthly.delta_mae])
    axes[0].axhline(0, color="#263a36", linewidth=.8)
    axes[0].set_xticks(monthly.month, [f"{month:02}\nn={count}" for month, count in zip(monthly.month, monthly.n)])
    axes[0].tick_params(axis="x", labelsize=8)
    axes[0].set(title="Diferencia mensual de MAE", xlabel="Mes de 2024 y casos evaluados",
                ylabel="MAE Ridge - MAE persistencia (µg/m³)")
    labels = ["Muestra completa", "Sin 5 fechas más favorables\npara Ridge",
              "Sin 5 fechas más desfavorables\npara Ridge"]
    axes[1].barh(labels, sensitivity.delta_mae, color=["#28715c", "#a34c20", "#28715c"])
    for index, row in enumerate(sensitivity.itertuples(index=False)):
        axes[1].text(.59, index, f"{row.delta_mae:+.3f} · n={row.n}", ha="right", va="center", fontsize=9)
    axes[1].axvline(0, color="#263a36", linewidth=.8)
    axes[1].invert_yaxis()
    axes[1].set(xlim=(-.42, .62), title="Sensibilidad global posterior a la prueba",
                xlabel="MAE Ridge - MAE persistencia (µg/m³)")
    fig.suptitle("Errores pareados de 2024 · diferencia negativa favorece a Ridge")
    fig.tight_layout()
    fig.savefig(ROOT / "docs/figures/analisis_errores_2024.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
