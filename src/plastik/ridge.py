"""Creates a ridge plot figure."""

import itertools
import attr
from typing import Any, Optional, Union

import matplotlib.gridspec as grid_spec
import matplotlib.pyplot as plt
import numpy as np
import plastik


@attr.s(auto_attribs=True)
class Ridge:
    """Plot data in a ridge plot with fixed width and fixed height per ridge.

    Parameters
    ----------
    data: list
        A list of n 2-tuples with (x, y)-pairs; list of n np.ndarrays: (y)
    options: str
        String with characters that set different options. This include 'b' (blank), 'c'
        (crop x-axis), 'g' (grid), 's' (slalom axis) and 'z' (squeeze). Blank removes all
        axis lines and turns the grid off. Crop sets the x-axis to the smallest common
        x-limit in all data tuples. Grid turns on the grid. Slalom axis make the y-axis
        ticks alternate between the left and right side. Squeeze makes each axis plot
        overlap by 50% (this turns slalom axis on, and makes two RHS ticks contiguous).
        The options are combined in a single string in arbitrary order. Any other
        characters than 'bcgsz' can be included without having any effect, the class with
        just look for existence of any of 'bcgsz'.
    y_scale: float
        Scale of y-axis relative to the default which decides the total height of the
        figure. Defaults to 1.
    xlabel: str
        x-label placed at the bottom.
    ylabel: str
        y-label for all y-axis.
    ylim: list
        List containing the upper and lower y-axis limit in all ridges.
    pltype: str
        plt class (loglog, plot, semilogx etc.) Defaults to plot.
    """

    data: list[Any] = attr.ib()

    @data.validator
    def _check_data_type(self, attribute, value):
        if not isinstance(value[0], tuple) and not isinstance(value[0], np.ndarray):
            raise TypeError(
                f"data must be a list of tuples or numpy arrays, not list of {type(self.data[0])}."
            )

    options: str = attr.ib(converter=str)
    y_scale: float = attr.ib(converter=float, default=1.0)
    xlabel: Optional[str] = attr.ib(converter=str, kw_only=True, default="")
    ylabel: Optional[str] = attr.ib(converter=str, kw_only=True, default="")
    ylim: list[float] = attr.Factory(list)
    pltype: str = attr.ib(converter=str, default="plot")
    colors = itertools.cycle(plt.rcParams["axes.prop_cycle"].by_key()["color"])

    def set_grid(self) -> None:
        fsize = (4, self.y_scale * len(self.data))
        self.gs = grid_spec.GridSpec(len(self.data), 1)
        self.__fig = plt.figure(figsize=fsize)
        # Set line type of horizontal grid lines
        self.gls = itertools.cycle(["-", "--"])
        self.ax_objs: list[plt.Axes] = []
        if "z" in self.options:
            self.gs.update(hspace=-0.5)
        else:
            self.gs.update(hspace=0.0)

    def set_xaxs(self) -> None:
        # if "xlim" in kwargs.keys():
        #     x_min, x_max = kwargs["xlim"]
        if len(self.data[0]) != 2:
            x_min, x_max = -0.5, len(self.data[0]) - 0.5
        elif "c" in self.options:
            x_min, x_max = self.__x_limit(False)
        else:
            x_min, x_max = self.__x_limit()
        self.xmin = x_min
        self.xmax = x_max

    def set_ylabel(
        self, y_min: Optional[float] = None, y_max: Optional[float] = None
    ) -> None:
        if y_min is None or y_max is None:
            self.ax = self.__fig.add_subplot(111, frame_on=False)
            self.ax.tick_params(
                labelcolor="w",
                axis="both",
                which="both",
                zorder=-1,  # labelleft=False,
                labelbottom=False,
                top=False,
                bottom=False,
                left=False,
                right=False,
            )
        else:
            self.ax.spines["top"].set_visible(False)
            self.ax.spines["bottom"].set_visible(False)
            self.ax.spines["left"].set_visible(False)
            self.ax.spines["right"].set_visible(False)
            self.pltype = (
                "log" if self.pltype in ["semilogy", "loglog"] else self.pltype
            )
            if self.pltype != "plot":
                self.ax.set_yscale(self.pltype)
            self.ax.set_ylabel(self.ylabel)
            y_min = 1e-3 if self.pltype == "log" and y_min <= 0 else y_min
            ylim = self.ylim or [y_min, y_max]
            self.ax.set_ylim(ylim)

    def __blank(self) -> None:
        spine = ["top", "bottom", "left", "right"]
        for sp in spine:
            self.ax_objs[-1].spines[sp].set_visible(False)
        plt.tick_params(
            axis="both",
            which="both",
            bottom=False,
            left=False,
            top=False,
            right=False,
            labelbottom=False,
            labelleft=False,
        )

    def __z_option(self, i) -> None:
        if i % 2:
            self.ax_objs[-1].tick_params(
                axis="y",
                which="both",
                left=False,
                labelleft=False,
                labelright=True,
            )
            self.ax_objs[-1].spines["left"].set_color("k")
        else:
            self.ax_objs[-1].tick_params(
                axis="y",
                which="both",
                right=False,
                labelleft=True,
                labelright=False,
            )
            self.ax_objs[-1].spines["right"].set_color("k")

    def __s_option(self, i) -> None:
        if i % 2:
            self.ax_objs[-1].tick_params(
                axis="y", which="both", labelleft=False, labelright=True
            )

    def __g_option(self, i) -> None:
        if ("g" in self.options and "z" not in self.options) or (
            "g" in self.options and len(self.data) == 1
        ):
            plt.grid(True, which="major", ls="-", alpha=0.2)
        elif "g" in self.options:
            plt.minorticks_off()
            alpha = 0.2 if i in (0, len(self.data) - 1) else 0.1
            plt.grid(True, axis="y", which="major", ls=next(self.gls), alpha=0.2)
            plt.grid(True, axis="x", which="major", ls="-", alpha=alpha)

    def __resolve_first_last_axis(self, i) -> None:
        if i == len(self.data) - 1:
            if self.xlabel:
                plt.xlabel(self.xlabel)
            if len(self.data) != 1:
                plt.tick_params(axis="x", which="both", top=False)
        elif i == 0:
            plt.tick_params(
                axis="x", which="both", bottom=False, labelbottom=False
            )  # , labeltop=True
        else:
            plt.tick_params(
                axis="x", which="both", bottom=False, top=False, labelbottom=False
            )

    def __resolve_options(self, i, spines, col) -> None:
        if len(self.data) != 1:
            if "z" in self.options:  # Squeeze
                self.__z_option(i)
            elif "s" in self.options:  # Slalom axis
                self.__s_option(i)
            for sp in spines:
                self.ax_objs[-1].spines[sp].set_visible(False)
            if "z" not in self.options:  # Squeeze
                self.ax_objs[-1].spines["left"].set_color(col)
                self.ax_objs[-1].spines["right"].set_color(col)
            self.ax_objs[-1].tick_params(axis="y", which="both", colors=col)
            self.ax_objs[-1].yaxis.label.set_color(col)
        self.__g_option(i)
        self.__resolve_first_last_axis(i)

    def __setup_axis(
        self,
        y_min: float,
        y_max: float,
        i: int,
        s: Union[tuple[np.ndarray, np.ndarray], np.ndarray],
    ) -> tuple[
        float, float, Union[tuple[np.ndarray, np.ndarray], np.ndarray], list[str]
    ]:
        self.ax_objs.append(self.__fig.add_subplot(self.gs[i : i + 1, 0:]))
        if i == 0:
            spines = ["bottom"]
        elif i == len(self.data) - 1:
            spines = ["top"]
        else:
            spines = ["top", "bottom"]
        s_ = s if isinstance(s, np.ndarray) else s[1]
        y_min = s_.min() if s_.min() < y_min else y_min
        y_max = s_.max() if s_.max() > y_max else y_max
        return y_min, y_max, s, spines

    def data_loop(self) -> tuple[float, float]:
        # Loop through data
        self.__lines = []
        y_min = np.inf
        y_max = -np.inf
        for i, s in enumerate(self.data):
            col = next(self.colors)
            # lnst = next(ls)
            y_min, y_max, s, spines = self.__setup_axis(y_min, y_max, i, s)

            # Plot data
            p_func = getattr(self.ax_objs[-1], self.pltype)
            line_type = "-o" if "d" in self.options else "-"
            # line_type = kwargs["lt"] if "lt" in kwargs.keys() else line_type
            # line_type = kwargs.pop("lt", line_type)
            # clr = kwargs["color"] if "color" in kwargs.keys() else col
            if len(s) == 2:
                ell = p_func(s[0], s[1], line_type, color=col, markersize=1.5)[0]
            else:
                ell = p_func(s, line_type, color=col, markersize=1.5)[0]

            # Append in line-list to create legend
            self.__lines.append(ell)
            # self.ax.add_line(ell)
            self.ax_objs[-1].patch.set_alpha(0)
            # Scale all subplots to the same x axis
            plt.xlim([self.xmin, self.xmax])
            if self.ylim:
                plt.ylim(self.ylim)

            # The length of data is greater than one, fix the plot according to the input
            # args and kwargs.
            if "b" in self.options:
                self.__blank()
            else:
                self.__resolve_options(i, spines, col)
        return y_min, y_max

    def __x_limit(self, maxx=True) -> tuple[float, float]:
        if isinstance(self.data[0], tuple):
            data: list[np.ndarray] = [d[0] for d in self.data]
        else:
            raise ValueError("'data' must have x-values.")
        t_min = data[0]
        x_max = data[0][-1]
        for t in data[1:]:
            t_0, t_max = np.min(t), np.max(t)
            if maxx:
                t_min = t if t_0 < t_min[0] else t_min
                # t_max = t if t_1 > t_max[-1] else t_max
                x_max = t_max if t_max > x_max else x_max
            else:
                t_min = t if t[0] > t_min[0] else t_min
                # t_max = t if t[-1] < t_max[-1] else t_max
                x_max = t_max if t_max < x_max else x_max
        diff = 0.05 * (x_max - t_min[0])
        # x_max = t_max[-1] + diff
        x_max += diff
        if self.pltype in ["loglog", "semilogx"]:
            x_min = 0.8 * t_min[t_min > 0][0] if t_min[0] < diff else t_min[0] - diff
            # if x_min < 0:
            #     x_min = 1e-10
        else:
            x_min = t_min[0] - diff
        return x_min, x_max

    @property
    def lines(self) -> list:
        return self.__lines

    @property
    def figure(self) -> plt.Figure:
        return self.__fig

    @property
    def top_axes(self) -> plt.Axes:
        return self.ax_objs[0]

    @property
    def bottom_axes(self) -> plt.Axes:
        return self.ax_objs[-1]

    @property
    def all_axes(self) -> list[plt.Axes]:
        return self.ax_objs

    def main(self) -> None:
        self.set_grid()
        self.set_xaxs()
        if self.ylabel:
            self.set_ylabel()
        y1, y2 = self.data_loop()
        if self.ylabel:
            self.set_ylabel(y1, y2)


if __name__ == "__main__":
    dta = [
        (np.array([1, 2, 3]), np.array([6, 5, 7])),
        (np.array([2, 3, 4]), np.array([10, 1, -200])),
        (np.array([2, 3, 4]), np.array([100, 1, -20])),
        (np.array([2, 3, 4]), np.array([100, 100, -200])),
        (np.array([2, 3, 4]), np.array([100, 1, -2])),
        (np.array([2, 3, 4]), np.array([1, 1, -200])),
    ]
    dta2 = [
        np.array([6, 5, 7]),
        np.array([10, 1, -200]),
        np.array([100, 1, -20]),
        np.array([100, 100, -200]),
        np.array([100, 1, -2]),
        np.array([1, 1, -200]),
    ]
    lab = [f"{i}" for i in range(6)]
    r = Ridge(dta, "gsz", ylabel="xlabel")
    r.main()
    f = r.figure
    l = r.lines
    a = r.top_axes
    axs = r.all_axes
    # a.legend(l, lab)
    plastik.topside_legends(a, l, lab, side="top")
    # for ax in axs:
    #     plastik.log_tick_format(ax, which="both")
    plt.show()
