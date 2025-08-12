import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse
import locale
from pathlib import Path
from matplotlib.ticker import FuncFormatter, FixedLocator
plt.rcParams.update({'font.size': 18})



def pick_sparse_ticks(values, min_distance=0.15):
    """Restituisce solo i valori abbastanza lontani (scala logaritmica) per asse X"""
    sparse_ticks = []
    last = None
    for v in sorted(values):
        if last is None or abs(np.log10(v) - np.log10(last)) > min_distance:
            sparse_ticks.append(v)
            last = v
    return sparse_ticks

def main():
    locale.setlocale(locale.LC_NUMERIC, 'C')
    parser = argparse.ArgumentParser(description="Reliability Plot: Unreliability vs Unavailability con scala logaritmica e tick distanziati")
    parser.add_argument("csv_file", help="Path al CSV di input")
    parser.add_argument("--no-show", action="store_true", help="Non mostrare il grafico a video")
    args = parser.parse_args()

    csv_path = Path(args.csv_file).expanduser().resolve()
    df = pd.read_csv(csv_path)

    ab_rowA = df[(df.Configuration == "A+B") & (df.Endpoint == "A")]
    ab_rowB = df[(df.Configuration == "A+B") & (df.Endpoint == "B")]
    if ab_rowA.empty or ab_rowB.empty:
        raise Exception("CSV deve contenere una configurazione 'A+B' per ciascun endpoint.")

    pool_size_target = int(ab_rowA["Pool Size"].values[0])
    df = df.copy()
    df['Unreliability'] = df['Reliability']

    y_values = set()
    x_values = set()

    # colors = plt.cm.tab10(np.linspace(0, 1, pool_size_target))

    # palette = sns.color_palette("Set1", n_colors=pool_size_target)
    # colors = palette

    # palette = [
    #     "#377eb8",  # blu
    #     "#e41a1c",  # rosso
    #     "#4daf4a",  # verde
    #     "#984ea3",  # viola
    #     "#ff7f00",  # arancione
    #     "#f781bf",  # rosa
    #     "#999999",  # grigio
    # ]

    # palette = [
    #     "#377eb8", "#e41a1c", "#4daf4a", "#984ea3",
    #     "#f781bf", "#999999", "#000000", "#17becf"
    # ]

    palette = [
        "#377eb8",  # blue
        "#e41a1c",  # red
        "#4daf4a",  # green
        "#984ea3",  # purple
        "#f781bf",  # pink
        "#999999",  # gray
        "#a65628",  # marrone
        "#000000",  # black
    ]
    palette = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
        "#bcbd22", "#17becf"
    
    ]

    while len(palette) < pool_size_target:
        palette += palette
    colors = palette[:pool_size_target]
    
    color_idx = 0
    pairs = []

    # Accoppia le configurazioni AxBy
    for a_size in range(1, pool_size_target):
        b_size = pool_size_target - a_size
        rowA = df[(df.Endpoint == "A") & (df.Configuration == "A") & (df["Pool Size"] == a_size)]
        rowB = df[(df.Endpoint == "B") & (df.Configuration == "B") & (df["Pool Size"] == b_size)]
        if not rowA.empty and not rowB.empty:
            pairs.append({
                "name": f"A{a_size}B{b_size}",
                "A": rowA.iloc[0],
                "B": rowB.iloc[0],
                "a_size": a_size,
                "b_size": b_size,
                "color": colors[color_idx % len(colors)]
            })
            color_idx += 1

    # Aggiungi coppia joined
    joinedA = df[(df.Configuration == "A+B") & (df.Endpoint == "A")].iloc[0]
    joinedB = df[(df.Configuration == "A+B") & (df.Endpoint == "B")].iloc[0]
    joined_pool_size = int(joinedA["Pool Size"])
    pairs.insert(0, {
        "name": "Joined",
        "A": joinedA,
        "B": joinedB,
        "a_size": joined_pool_size,
        "b_size": joined_pool_size,
        "color": "blue"
    })

    # Raccogli tutti i valori per i tick
    for p in pairs:
        x_values.add(p["A"]["Unreliability"])
        x_values.add(p["B"]["Unreliability"])
        y_values.add(p["A"]["Unavailability"])
        y_values.add(p["B"]["Unavailability"])

    # Tick X distanziati, solo i nostri!
    chosen_x_ticks = pick_sparse_ticks(x_values, min_distance=0.015)

    fig, ax = plt.subplots(figsize=(14, 9))
    legend_handles, legend_labels = [], []

    # Disegna linee e punti
    for p in pairs:
        c = p['color']
        ax.plot([p["A"]["Unreliability"], p["B"]["Unreliability"]],
                [p["A"]["Unavailability"], p["B"]["Unavailability"]],
                color=c, linewidth=2.5, alpha=0.5, zorder=1)
        ax.scatter(p["A"]["Unreliability"], p["A"]["Unavailability"],
                  color=c, s=120, zorder=5, edgecolors='white', linewidth=1)
        ax.scatter(p["B"]["Unreliability"], p["B"]["Unavailability"],
                  color=c, facecolors='none', edgecolors=c, s=120, linewidth=2.5, zorder=5)

    # Etichette vicino ai punti
    for p in pairs:
        c = p['color']
        label_a = f"A{p['a_size']}"
        label_b = f"B{p['b_size']}"
        ax.annotate(label_a, (p["A"]["Unreliability"], p["A"]["Unavailability"]),
                    color=c, fontsize=16, fontweight="bold", zorder=10,
                    xytext=(-15, -15), textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9,
                              edgecolor=c, linewidth=1.2))
        ax.annotate(label_b, (p["B"]["Unreliability"], p["B"]["Unavailability"]),
                    color=c, fontsize=16, fontweight="bold", zorder=10,
                    xytext=(6, 6), textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9,
                              edgecolor=c, linewidth=1.2))
        legend_handles.append(plt.Line2D([0], [0], marker='o', color=c, linestyle='-', 
                                         markersize=8, linewidth=1))
        legend_labels.append(p["name"])

    # Configura assi SOLO con i nostri tick!
    ax.set_xscale('log')
    ax.set_xticks(chosen_x_ticks, minor=False)
    ax.set_xticks([], minor=True)
    ax.xaxis.set_major_locator(FixedLocator(chosen_x_ticks))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: "{:.5f}".format(x) if x else ""))
    ax.set_xticklabels([f"{x:.5f}" for x in chosen_x_ticks], rotation=45, ha='right')
    ax.set_xlabel("Unreliability (Log Scale)", fontsize=18, fontweight="bold")
    ax.set_ylabel("Unavailability", fontsize=18, fontweight="bold")
    ax.grid(True, which="both", linestyle="--", alpha=0.2, zorder=0)

    # Y ticks come sempre
    y_sorted = sorted(y_values)
    max_ticks_y = 5
    if len(y_sorted) > max_ticks_y:
        step_y = max(1, len(y_sorted) // max_ticks_y)
        y_ticks = y_sorted[::step_y]
        if y_sorted[-1] not in y_ticks:
            y_ticks.append(y_sorted[-1])
    else:
        y_ticks = y_sorted
    ax.set_yticks(y_ticks)
    ax.set_yticklabels([f"{y:.5f}" for y in y_ticks], fontsize=18)

    ax.legend(legend_handles, legend_labels, 
              loc="center left", bbox_to_anchor=(1.02, 0.5), 
              fontsize=16, frameon=True, fancybox=True, shadow=True)

    plt.subplots_adjust(bottom=0.20, right=0.82, top=0.95)
    outpath = csv_path.parent / f"{csv_path.stem}_reliability_clean_plot.pdf"
    plt.savefig(outpath, bbox_inches='tight', dpi=300, facecolor='white')
    print(f"✓ Plot salvato in: {outpath}")
    print(f"✓ Configurazioni generate:")
    for p in pairs:
        print(f"  - {p['name']}: A{p['a_size']} + B{p['b_size']}")
    if not args.no_show:
        plt.show()

if __name__ == "__main__":
    main()