import math

import matplotlib.pyplot
import matplotlib.ticker
import pandas
import seaborn

from app import models

# WARNING: THERE BE DRAGONS, THE FOLLOWING CODE IS PARTLY AI GENERATED 🐉


def generate_line_graph(
    node_resp: list[models.models.NodeResponseBenchRpc], title: str, with_error: bool = False
):
    """
    Generates a line graph using Seaborn showing min, max, and average values
    Args:
        data_series: Dictionary where keys are line labels and values are lists of (min, max, avg) tuples
    Returns:
        matplotlib figure object
    """
    seaborn.set_style(
        "whitegrid",
        {
            "axes.facecolor": "#ffffff",
            "figure.facecolor": "#ffffff",
            "grid.color": "#E5E5E5",  # Light gray grid
            "axes.edgecolor": "#666666",  # Darker edge color for remaining spines
            "axes.linewidth": 1.2,  # Slightly thicker spines
        },
    )

    # Create a DataFrame suitable for multiple lines with error bands. Responses
    # are in nanoseconds so we convert this this to microseconds to be more
    # readable
    df_rows = [
        {
            "x_value": resp.block_number,
            "min_value": resp.elapsed_low // 1_000,
            "max_value": resp.elapsed_high // 1_000,
            "average": resp.elapsed_avg // 1_000,
            "series": resp.node,
        }
        for resp in node_resp
    ]

    data = pandas.DataFrame(df_rows)
    fig, ax = matplotlib.pyplot.subplots(figsize=(15, 8), dpi=100)

    for idx, label in enumerate(data["series"].unique()):
        series_data = data[data["series"] == label]
        color = seaborn.color_palette()[idx]

        # Plot the error band
        if with_error:
            ax.fill_between(
                series_data["x_value"],
                series_data["min_value"],
                series_data["max_value"],
                alpha=0.15,
                color=color,
                label=f"{label} (range)",
                zorder=1,
            )

        # Plot the average line
        ax.plot(
            series_data["x_value"],
            series_data["average"],
            linewidth=2.5,
            label=f"{label} (average)",
            color=color,
            zorder=2,
        )

        # Add markers
        ax.scatter(series_data["x_value"], series_data["average"], s=10, color=color, alpha=1)

    # Customize spines
    seaborn.set_context("paper")
    seaborn.despine(fig=fig, ax=ax, top=True, right=True, left=False, bottom=False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_linewidth(1.2)
        ax.spines[spine].set_color("#666666")

    # Set title
    ax.set_title(title, pad=20, fontsize=14, fontweight="bold", color="#333333")

    # Customize tick labels
    ax.tick_params(axis="both", labelsize=10, colors="#333333")

    # Format axes
    ax.set_xlabel("Block Number", fontsize=12, labelpad=10, color="#333333")
    ax.set_ylabel("Latency (μs)", fontsize=12, labelpad=10, color="#333333")

    ymax = max([resp.elapsed_avg for resp in node_resp]) // 1_000
    xmax = max([resp.block_number for resp in node_resp])
    ax.set_ylim(0, ymax * 1.5)
    ax.set_xlim(0, xmax)

    formatter = lambda x, _: format(int(x), ",")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(formatter))
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(formatter))

    # Format the grid
    ylocator = 10 ** (round(math.log10(ymax)) - 1)
    xlocator = 10 ** (round(math.log10(xmax)) - 1)

    # auto-scaling for the axes around the closest power of 10, should work well
    # enough in most situations
    ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(ylocator))
    ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(xlocator))
    ax.grid(True, which="major", color="#E5E5E5", linestyle="-", linewidth=0.8, alpha=0.5)

    ax.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(2))
    ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(2))
    ax.grid(True, which="minor", color="#F5F5F5", linestyle=":", linewidth=0.5, alpha=0.3)

    # Format legend
    legend = ax.legend(
        title="Node",
        title_fontsize=11,
        fontsize=10,
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        borderaxespad=0,
        frameon=True,
        fancybox=True,
        shadow=False,
        framealpha=0.95,
    )
    legend.get_frame().set_linewidth(0.5)
    legend.get_frame().set_edgecolor("#cccccc")

    # Adjust layout to prevent label cutoff
    fig.tight_layout()

    return fig
