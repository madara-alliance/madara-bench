import math
from typing import TypeVar

import matplotlib.axes
import matplotlib.figure
import matplotlib.pyplot
import matplotlib.ticker
import pandas
import seaborn

from app import database, models

# WARNING: THERE BE DRAGONS, THE FOLLOWING CODE IS PARTLY AI GENERATED 🐉


T = TypeVar("T")


def common_filter(node_resp: list[T], threshold: int) -> list[T]:
    if threshold >= 100 or threshold < 0:
        return node_resp

    take = int(len(node_resp) * (threshold / 100))
    return node_resp[:take]


def common_style():
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
    colors = ["#2C7BB6", "#FF8C00", "#2ECC71"]
    seaborn.set_palette(colors)


def common_title(ax: matplotlib.axes.Axes, title: str):
    ax.set_title(title, pad=20, fontsize=14, fontweight="bold", color="#333333")


def common_spines(ax: matplotlib.axes.Axes, fig: matplotlib.figure.Figure):
    seaborn.set_context("paper")
    seaborn.despine(fig=fig, ax=ax, top=True, right=True, left=False, bottom=False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_linewidth(1.2)
        ax.spines[spine].set_color("#666666")


def common_axes(
    ax: matplotlib.axes.Axes,
    xmin: float | int,
    xmax: float | int,
    ymin: float | int,
    ymax: float | int,
    xlabel: str,
    ylabel: str,
):
    ax.tick_params(axis="both", labelsize=10, colors="#333333")

    ax.set_xlabel(xlabel, fontsize=12, labelpad=10, color="#333333")
    ax.set_ylabel(ylabel, fontsize=12, labelpad=10, color="#333333")

    ax.set_ylim(ymin, ymax)
    ax.set_xlim(xmin, xmax)

    formatter = lambda x, _: format(int(x), ",")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(formatter))
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(formatter))


def common_grid(ax: matplotlib.axes.Axes, xmax: float | int, ymax: float | int):
    xlocator = 10 ** (round(math.log10(xmax)) - 1)
    ylocator = 10 ** (round(math.log10(ymax)) - 1)

    if xmax // xlocator > 12:
        xlocator *= 2
    if ymax // ylocator > 12:
        ylocator *= 2

    # auto-scaling for the axes around the closest power of 10, should work well
    # enough in most situations
    ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(xlocator))
    ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(ylocator))
    ax.grid(True, which="major", color="#E5E5E5", linestyle="-", linewidth=0.8, alpha=0.5)

    ax.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(2))
    ax.grid(True, which="minor", color="#F5F5F5", linestyle=":", linewidth=0.5, alpha=0.3)


def common_legend(ax: matplotlib.axes.Axes):
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


def generate_line_graph_rpc(
    node_resp: list[models.models.NodeResponseBenchRpc],
    title: str,
    with_error: bool = False,
    threshold: int = 100,
):
    common_style()

    node_resp = sorted(node_resp, key=lambda x: x.elapsed_avg)
    node_resp = common_filter(node_resp, threshold)
    node_resp = sorted(node_resp, key=lambda x: x.block_number)

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

    for label in sorted(data["series"].unique()):
        series_data = data[data["series"] == label]
        color = seaborn.color_palette()[database.models.NodeDB.from_model_bench(label)]

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

    # Set title
    common_title(ax, title)

    # Customize spines
    common_spines(ax, fig)

    # Format axes
    ymax = max([resp.elapsed_avg for resp in node_resp]) // 1_000
    xmax = max([resp.block_number for resp in node_resp])
    common_axes(ax, 0, xmax, 0, ymax * 1.5, "Block number", "Latency (μs)")

    # Format the grid
    common_grid(ax, xmax, ymax)

    # Format legend
    common_legend(ax)

    # Adjust layout to prevent label cutoff
    fig.tight_layout()

    return fig


def generate_line_graph_sys(
    node_resp: list[models.models.ResponseModelSystem],
    metrics: models.models.SystemMetric,
    title: str,
    threshold: int = 100,
):
    common_style()

    node_resp = sorted(node_resp, key=lambda x: x.value)
    node_resp = common_filter(node_resp, threshold)
    node_resp = sorted(node_resp, key=lambda x: x.block_number)

    # Create a DataFrame suitable for multiple lines with error bands. Responses
    # are in nanoseconds so we convert this this to microseconds to be more
    # readable
    match metrics:
        case models.models.SystemMetric.CPU_SYSTEM:
            df_rows = [
                {
                    "x_value": resp.block_number,
                    "average": resp.value / 100,
                    "series": resp.node,
                }
                for resp in node_resp
            ]
            ymin = 0
            ymax = max([resp.value for resp in node_resp]) / 100 * 1.5
            ylabel = "System usage (%)"
        case models.models.SystemMetric.MEMORY:
            df_rows = [
                {
                    "x_value": resp.block_number,
                    "average": resp.value // 1_000,
                    "series": resp.node,
                }
                for resp in node_resp
            ]
            ymin = min([resp.value for resp in node_resp]) // 1_000 * 0.8
            ymax = max([resp.value for resp in node_resp]) // 1_000 * 1.2
            ylabel = "RAM usage (Kb)"
        case models.models.SystemMetric.STORAGE:
            df_rows = [
                {
                    "x_value": resp.block_number,
                    "average": resp.value // 1_000,
                    "series": resp.node,
                }
                for resp in node_resp
            ]
            ymin = min([resp.value for resp in node_resp]) // 1_000 * 0.8
            ymax = max([resp.value for resp in node_resp]) // 1_000 * 1.2
            ylabel = "Disk space (Kb)"

    data = pandas.DataFrame(df_rows)
    fig, ax = matplotlib.pyplot.subplots(figsize=(15, 8), dpi=100)

    for label in sorted(data["series"].unique()):
        series_data = data[data["series"] == label]
        color = seaborn.color_palette()[database.models.NodeDB.from_model_bench(label)]

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

    # Set title
    common_title(ax, title)

    # Customize spines
    common_spines(ax, fig)

    # Format axes
    xmax = max([resp.block_number for resp in node_resp])
    common_axes(ax, 0, xmax, ymin, ymax, "Block number", ylabel)

    # Format the grid
    common_grid(ax, xmax, ymax)

    # Format legend
    common_legend(ax)

    # Adjust layout to prevent label cutoff
    fig.tight_layout()

    return fig
