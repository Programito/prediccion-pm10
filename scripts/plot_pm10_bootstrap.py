"""Render bootstrap intervals using the notebook plotting dependencies."""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent


def main():
    rows = pd.read_csv(ROOT / "output/pm10_bootstrap/intervalos.csv", dtype={"station": str})
    limit = max(rows.lower.abs().max(), rows.upper.abs().max()) * 1.12
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 10})
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True)
    for ax, (station, group) in zip(axes.flat, rows.groupby("station", sort=False), strict=True):
        group = group.sort_values("block_days")
        positions = list(range(len(group)))
        ax.hlines(positions, group.lower, group.upper, color="#28715c", linewidth=3)
        ax.plot(group.estimate, positions, "o", color="#263a36", markersize=5)
        ax.axvline(0, color="#6a7772", linestyle="--", linewidth=1)
        ax.set_yticks(positions, [f"{days} días" for days in group.block_days])
        ax.invert_yaxis()
        ax.set(title=f"{group.name.iloc[0].title()} · n={group.n.iloc[0]}", xlim=(-limit, limit), ylim=(2.5, -.5))
        ax.grid(axis="x", alpha=.2)
    for ax in axes[1]:
        ax.set_xlabel("MAE Ridge - MAE persistencia (µg/m³)")
    fig.suptitle("Bootstrap por bloques · intervalos percentiles nominales del 95 %\n5.000 réplicas por longitud · estaciones sincronizadas por fecha")
    fig.tight_layout()
    fig.savefig(ROOT / "docs/figures/incertidumbre_mae_2024.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
