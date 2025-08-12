import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Reliability Plot: Unreliability vs Unavailability con etichette migliorate")
    parser.add_argument("csv_file", help="Path al CSV di input")
    parser.add_argument("--no-show", action="store_true", help="Non mostrare il grafico a video")
    args = parser.parse_args()

    csv_path = Path(args.csv_file).expanduser().resolve()
    df = pd.read_csv(csv_path)

    # Pool size target dalla configurazione joined
    ab_rowA = df[(df.Configuration == "A+B") & (df.Endpoint == "A")]
    ab_rowB = df[(df.Configuration == "A+B") & (df.Endpoint == "B")]

    if ab_rowA.empty or ab_rowB.empty:
        raise Exception("CSV deve contenere una configurazione 'A+B' per ciascun endpoint.")

    pool_size_target = int(ab_rowA["Pool Size"].values[0])

    # Rinomina Reliability ad Unreliability (senza sottrazione)
    df = df.copy()
    df['Unreliability'] = df['Reliability']

    # Prepara dati per plot e ticks
    x_values, y_values = set(), set()

    # Accoppia le configurazioni AxBy
    colors = plt.cm.tab10(np.linspace(0, 1, pool_size_target))
    color_idx = 0
    pairs = []

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

    # Plot con figura più grande
    fig, ax = plt.subplots(figsize=(14, 9))
    legend_handles, legend_labels = [], []

    # Prima disegna tutte le linee (z-order basso)
    for p in pairs:
        c = p['color']
        ax.plot([p["A"]["Unreliability"], p["B"]["Unreliability"]],
                [p["A"]["Unavailability"], p["B"]["Unavailability"]],
                color=c, linewidth=1.0, alpha=0.5, zorder=1)

    # Poi disegna i punti (z-order medio)
    for p in pairs:
        c = p['color']
        ax.scatter(p["A"]["Unreliability"], p["A"]["Unavailability"], 
                  color=c, s=120, zorder=5, edgecolors='white', linewidth=1)
        ax.scatter(p["B"]["Unreliability"], p["B"]["Unavailability"], 
                  color=c, facecolors='none', edgecolors=c, s=120, linewidth=2.5, zorder=5)

    # Infine disegna le etichette (z-order alto) - PIÙ VICINE AI PUNTI
    for p in pairs:
        c = p['color']
        # Etichetta per endpoint A con pool size
        if p["name"] == "Joined":
            label_a = f"A{p['a_size']}"
            label_b = f"B{p['b_size']}"
        else:
            label_a = f"A{p['a_size']}"
            label_b = f"B{p['b_size']}"

        # Etichette molto più vicine ai punti
        ax.annotate(label_a, (p["A"]["Unreliability"], p["A"]["Unavailability"]), 
                    color=c, fontsize=10, fontweight="bold", zorder=10,
                    xytext=(-8, -6), textcoords="offset points",  # Offset ridotto!
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9, 
                             edgecolor=c, linewidth=1.2))
        ax.annotate(label_b, (p["B"]["Unreliability"], p["B"]["Unavailability"]), 
                    color=c, fontsize=10, fontweight="bold", zorder=10,
                    xytext=(6, 6), textcoords="offset points",    # Offset ridotto!
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9, 
                             edgecolor=c, linewidth=1.2))

        # Legenda
        legend_handles.append(plt.Line2D([0], [0], marker='o', color=c, linestyle='-', 
                                       markersize=8, linewidth=1))
        legend_labels.append(p["name"])

    # Config assi
    ax.set_xlabel("Unreliability", fontsize=13, fontweight="bold")
    ax.set_ylabel("Unavailability", fontsize=13, fontweight="bold")
    # ax.set_title("Unreliability vs Unavailability", fontsize=15, fontweight="bold", pad=25)
    ax.grid(True, linestyle="--", alpha=0.2, zorder=0)

    # Ottimizzazione tick per evitare sovrapposizioni
    x_sorted = sorted(x_values)
    y_sorted = sorted(y_values)

    # Seleziona un sottoinsieme di tick per evitare affollamento
    max_ticks_x = 6
    max_ticks_y = 5  

    # Per X: prendi ogni N-esimo valore se ce ne sono troppi
    if len(x_sorted) > max_ticks_x:
        step_x = max(1, len(x_sorted) // max_ticks_x)
        x_ticks = x_sorted[::step_x]
        if x_sorted[-1] not in x_ticks:
            x_ticks.append(x_sorted[-1])
    else:
        x_ticks = x_sorted

    # Per Y: prendi ogni N-esimo valore se ce ne sono troppi
    if len(y_sorted) > max_ticks_y:
        step_y = max(1, len(y_sorted) // max_ticks_y)
        y_ticks = y_sorted[::step_y]
        if y_sorted[-1] not in y_ticks:
            y_ticks.append(y_sorted[-1])
    else:
        y_ticks = y_sorted

    # Imposta i tick con formattazione migliorata
    ax.set_xticks(x_ticks)
    ax.set_yticks(y_ticks)

    # Formattazione con 5 cifre decimali
    ax.set_xticklabels([f"{x:.5f}" for x in x_ticks], fontsize=9, rotation=45, ha='right')
    ax.set_yticklabels([f"{y:.5f}" for y in y_ticks], fontsize=9)

    # Legenda posizionata meglio
    ax.legend(legend_handles, legend_labels, 
             loc="center left", bbox_to_anchor=(1.02, 0.5), 
             fontsize=11, frameon=True, fancybox=True, shadow=True)

    # Layout con più spazio
    plt.subplots_adjust(bottom=0.15, right=0.82, top=0.92)

    # Salva
    outpath = csv_path.parent / f"{csv_path.stem}_reliability_plot.pdf"
    plt.savefig(outpath, bbox_inches='tight', dpi=300, facecolor='white')
    print(f"✓ Plot salvato in: {outpath}")

    print(f"✓ Configurazioni generate:")
    for p in pairs:
        if p["name"] == "Joined":
            print(f"  - {p['name']}: A{p['a_size']} + B{p['b_size']}")
        else:
            print(f"  - {p['name']}: A{p['a_size']} + B{p['b_size']}")

    if not args.no_show:
        plt.show()

if __name__ == "__main__":
    main()
