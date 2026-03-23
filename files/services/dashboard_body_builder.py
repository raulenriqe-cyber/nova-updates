from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget


@dataclass
class DashboardBodyRefs:
    status_label: Any
    sentiment_label: Any
    symbol_label: Any
    chart: Any
    gauge: Any
    fields: dict[str, Any]
    llm_widgets: dict[str, dict[str, Any]]
    network_labels: dict[str, Any]
    network_dots: dict[str, Any]
    llm_network_dots: list[Any]
    sections: dict[str, Any]
    groups: dict[str, Any]


class DashboardBodyBuilder:
    def __init__(
        self,
        *,
        theme: dict[str, str],
        llm_names: list[str],
        llm_full: dict[str, tuple[str, str]],
        label_factory: Callable[..., Any],
        section_factory: Callable[[str], Any],
        separator_factory: Callable[[], Any],
        progress_factory: Callable[..., Any],
        chart_factory: Callable[[str], Any],
        gauge_factory: Callable[[], Any],
        roi_gauge_factory: Callable[[], Any],
        roi_bar_factory: Callable[[], Any],
    ):
        self.theme = theme
        self.llm_names = llm_names
        self.llm_full = llm_full
        self.label_factory = label_factory
        self.section_factory = section_factory
        self.separator_factory = separator_factory
        self.progress_factory = progress_factory
        self.chart_factory = chart_factory
        self.gauge_factory = gauge_factory
        self.roi_gauge_factory = roi_gauge_factory
        self.roi_bar_factory = roi_bar_factory

    def _wrap(self, *items: Any) -> QWidget:
        container = QWidget()
        container.setAttribute(Qt.WA_NoSystemBackground)
        container.setStyleSheet("background:transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        for item in items:
            if isinstance(item, QWidget):
                layout.addWidget(item)
            else:
                layout.addLayout(item)
        return container

    def build(
        self,
        *,
        body_layout: QVBoxLayout,
        texts: dict,
        accent_color: str,
        footer_text: str,
    ) -> DashboardBodyRefs:
        fields: dict[str, Any] = {}
        groups: dict[str, Any] = {}
        sections: dict[str, Any] = {}

        status_row = QHBoxLayout()
        status_row.setSpacing(8)
        status_row.setContentsMargins(0, 0, 0, 2)
        status_label = self.label_factory(texts["connecting"], self.theme["dim2"], 10)
        sentiment_label = self.label_factory("◆ NEUTRAL", self.theme["dim2"], 12, True)
        symbol_label = self.label_factory("", self.theme["dim"], 9)
        status_row.addWidget(status_label, 1)
        status_row.addWidget(sentiment_label)
        body_layout.addLayout(status_row)

        chart = self.chart_factory(accent_color)
        body_layout.addWidget(chart)
        body_layout.addSpacing(2)

        sections["_sec_market"] = self.section_factory(texts["sec_market"])
        market_row = QHBoxLayout()
        market_row.setSpacing(4)
        market_row.setContentsMargins(0, 0, 0, 0)
        for name in ["Bid", "Ask", "Spread", "Session", "Regime"]:
            market_row.addWidget(self.label_factory(name, self.theme["dim"], 9, mono=False))
            value = self.label_factory("—", self.theme["text2"], 11)
            fields[name] = value
            market_row.addWidget(value)
            if name != "Regime":
                market_row.addSpacing(6)
        market_row.addStretch()
        groups["_grp_market"] = self._wrap(sections["_sec_market"], market_row, self.separator_factory())
        body_layout.addWidget(groups["_grp_market"])

        sections["_sec_ind"] = self.section_factory(texts["sec_indicators"])
        indicator_row_1 = QHBoxLayout()
        indicator_row_1.setSpacing(4)
        indicator_row_1.setContentsMargins(0, 0, 0, 0)
        indicator_row_1.addWidget(self.label_factory("RSI", self.theme["dim"], 9, mono=False))
        fields["RSI"] = self.label_factory("—", self.theme["warn"], 11, True)
        indicator_row_1.addWidget(fields["RSI"])
        fields["rsi_bar"] = self.progress_factory(self.theme["warn"], 5)
        fields["rsi_bar"].setFixedWidth(70)
        indicator_row_1.addWidget(fields["rsi_bar"])
        indicator_row_1.addSpacing(8)
        indicator_row_1.addWidget(self.label_factory("ADX", self.theme["dim"], 9, mono=False))
        fields["ADX"] = self.label_factory("—", self.theme["text2"], 11)
        indicator_row_1.addWidget(fields["ADX"])
        indicator_row_1.addSpacing(6)
        indicator_row_1.addWidget(self.label_factory("MACD", self.theme["dim"], 9, mono=False))
        fields["MACD"] = self.label_factory("—", self.theme["text2"], 11)
        indicator_row_1.addWidget(fields["MACD"])
        indicator_row_1.addStretch()

        indicator_row_2 = QHBoxLayout()
        indicator_row_2.setSpacing(4)
        indicator_row_2.setContentsMargins(0, 0, 0, 0)
        for name, label in [("ATR", "ATR"), ("Stoch", "Stoch"), ("BB W", "BB W")]:
            indicator_row_2.addWidget(self.label_factory(label, self.theme["dim"], 9, mono=False))
            value = self.label_factory("—", self.theme["text2"], 11)
            fields[name] = value
            indicator_row_2.addWidget(value)
            indicator_row_2.addSpacing(8)
        indicator_row_2.addStretch()
        groups["_grp_ind"] = self._wrap(sections["_sec_ind"], indicator_row_1, indicator_row_2, self.separator_factory())
        body_layout.addWidget(groups["_grp_ind"])

        sections["_sec_ml"] = self.section_factory(texts["sec_ml"])
        ml_row = QHBoxLayout()
        ml_row.setSpacing(4)
        ml_row.setContentsMargins(0, 0, 0, 0)
        for name in ["DNN", "LSTM", "RL", "Bayesian"]:
            ml_row.addWidget(self.label_factory(name, self.theme["dim"], 9, mono=False))
            value = self.label_factory("—", self.theme["text2"], 11)
            fields[f"ml_{name}"] = value
            ml_row.addWidget(value)
            ml_row.addSpacing(6)
        ml_row.addStretch()
        fields["ml_pred"] = self.label_factory("Pred NEUTRAL", self.theme["dim"], 10)
        ml_row.addWidget(fields["ml_pred"])

        bull_bear_row = QHBoxLayout()
        bull_bear_row.setSpacing(6)
        bull_bear_row.setContentsMargins(0, 0, 0, 0)
        fields["bull"] = self.label_factory("Bull 50%", self.theme["buy"], 11, True)
        fields["bear"] = self.label_factory("Bear 50%", self.theme["sell"], 11, True)
        bull_bear_row.addWidget(fields["bull"])
        bull_bear_row.addWidget(fields["bear"])
        bull_bear_row.addStretch()
        fields["bull_bar"] = self.progress_factory(self.theme["buy"], 5)
        groups["_grp_ml"] = self._wrap(sections["_sec_ml"], ml_row, bull_bear_row, fields["bull_bar"], self.separator_factory())
        body_layout.addWidget(groups["_grp_ml"])

        sections["_sec_brain"] = self.section_factory(texts["sec_brain"])
        legend_row = QHBoxLayout()
        legend_row.setSpacing(6)
        legend_row.setContentsMargins(0, 0, 0, 2)
        for dot_char, dot_color, dot_label in [
            ("●", self.theme["buy"], texts["legend_on"]),
            ("◐", self.theme["warn"], texts["legend_wait"]),
            ("○", self.theme["error"], texts["legend_off"]),
        ]:
            legend_row.addWidget(self.label_factory(f"{dot_char} {dot_label}", dot_color, 8, mono=False))
        legend_row.addSpacing(8)
        legend_row.addWidget(self.label_factory("│", self.theme["dim"], 8, mono=False))
        legend_row.addSpacing(4)
        for vote_color, vote_text in [
            (self.theme["buy"], "BUY"),
            (self.theme["sell"], "SELL"),
            (self.theme["dim2"], "HOLD"),
        ]:
            legend_row.addWidget(self.label_factory(vote_text, vote_color, 8, True))
            legend_row.addSpacing(2)
        legend_row.addStretch()

        llm_widgets: dict[str, dict[str, Any]] = {}
        llm_rows: list[QHBoxLayout] = []
        for row_start in [0, 6]:
            llm_row = QHBoxLayout()
            llm_row.setSpacing(0)
            llm_row.setContentsMargins(0, 0, 0, 2)
            for i in range(row_start, min(row_start + 6, 12)):
                name = self.llm_names[i]
                full_name, role = self.llm_full.get(name, (name, ""))
                dot = self.label_factory("●", self.theme["dim"], 11)
                dot.setFixedWidth(12)
                short_name = self.label_factory(full_name[:7], self.theme["dim2"], 8, mono=False)
                short_name.setMaximumWidth(42)
                short_name.setMinimumWidth(0)
                short_name.setToolTip(f"{full_name}\n{role}")
                dot.setToolTip(f"{full_name} — {role}")
                state = self.label_factory("─", self.theme["dim"], 9, True)
                state.setMaximumWidth(28)
                state.setMinimumWidth(0)
                llm_widgets[name] = {"dot": dot, "state": state}
                cell = QHBoxLayout()
                cell.setSpacing(1)
                cell.setContentsMargins(0, 0, 4, 0)
                cell.addWidget(dot)
                cell.addWidget(short_name)
                cell.addWidget(state)
                llm_row.addLayout(cell)
            llm_row.addStretch()
            llm_rows.append(llm_row)

        consensus_row = QHBoxLayout()
        consensus_row.setSpacing(6)
        consensus_row.setContentsMargins(0, 2, 0, 0)
        fields["consensus"] = self.label_factory("CONSENSUS HOLD", self.theme["hold"], 11, True)
        fields["cons_pct"] = self.label_factory("0%", self.theme["dim"], 11)
        fields["quality"] = self.label_factory("Q 0%", self.theme["dim"], 10)
        fields["timing"] = self.label_factory("T 1.00x", self.theme["dim"], 10)
        fields["rr"] = self.label_factory("R/R 0:1", self.theme["dim"], 10)
        consensus_row.addWidget(fields["consensus"])
        consensus_row.addWidget(fields["cons_pct"])
        consensus_row.addStretch()
        consensus_row.addWidget(fields["quality"])
        consensus_row.addWidget(fields["timing"])
        consensus_row.addWidget(fields["rr"])
        fields["cons_bar"] = self.progress_factory(self.theme["hold"], 6)
        groups["_grp_brain"] = self._wrap(
            sections["_sec_brain"],
            legend_row,
            *llm_rows,
            consensus_row,
            fields["cons_bar"],
            self.separator_factory(),
        )
        body_layout.addWidget(groups["_grp_brain"])

        sections["_sec_pat"] = self.section_factory(texts["sec_patterns"])
        pattern_row = QHBoxLayout()
        pattern_row.setSpacing(4)
        pattern_row.setContentsMargins(0, 0, 0, 0)
        fields["pat"] = self.label_factory("Scanning…", self.theme["dim2"], 9)
        fields["pat_b"] = self.label_factory("▲Bull 0", self.theme["buy"], 10, True)
        fields["pat_r"] = self.label_factory("▼Bear 0", self.theme["sell"], 10, True)
        pattern_row.addWidget(fields["pat"], 1)
        pattern_row.addWidget(fields["pat_b"])
        pattern_row.addWidget(fields["pat_r"])
        groups["_grp_pat"] = self._wrap(sections["_sec_pat"], pattern_row, self.separator_factory())
        body_layout.addWidget(groups["_grp_pat"])

        sections["_sec_atk"] = self.section_factory(texts["sec_attack"])
        attack_row = QHBoxLayout()
        attack_row.setSpacing(8)
        attack_row.setContentsMargins(0, 0, 0, 0)
        gauge = self.gauge_factory()
        attack_row.addWidget(gauge)
        attack_info = QVBoxLayout()
        attack_info.setSpacing(4)
        attack_info.setContentsMargins(0, 0, 0, 0)
        fields["atk_icon"] = self.label_factory("○ IDLE", self.theme["dim"], 12, True)
        fields["atk_pct_lbl"] = self.label_factory("0.0%", self.theme["dim"], 18, True)
        fields["atk_dir"] = self.label_factory("Dir NONE", self.theme["dim"], 10)
        fields["atk_cool"] = self.label_factory("CD 0.0s", self.theme["warn"], 10)
        attack_info.addWidget(fields["atk_icon"])
        attack_info.addWidget(fields["atk_pct_lbl"])
        attack_sub_row = QHBoxLayout()
        attack_sub_row.setSpacing(8)
        attack_sub_row.addWidget(fields["atk_dir"])
        attack_sub_row.addWidget(fields["atk_cool"])
        attack_sub_row.addStretch()
        attack_info.addLayout(attack_sub_row)
        attack_row.addLayout(attack_info, 1)
        fields["atk_bar"] = self.progress_factory(self.theme["warn"], 7)
        groups["_grp_atk"] = self._wrap(sections["_sec_atk"], attack_row, fields["atk_bar"], self.separator_factory())
        body_layout.addWidget(groups["_grp_atk"])

        sections["_sec_of"] = self.section_factory(texts["sec_orderflow"])
        orderflow_row = QHBoxLayout()
        orderflow_row.setSpacing(4)
        orderflow_row.setContentsMargins(0, 0, 0, 0)
        for name, label in [("Buy", "Buy"), ("Sell", "Sell"), ("Delta", "Δ"), ("Imbalance", "Imb"), ("CVD", "CVD")]:
            orderflow_row.addWidget(self.label_factory(label, self.theme["dim"], 9, mono=False))
            value = self.label_factory("0", self.theme["text2"], 11)
            fields[f"of_{name}"] = value
            orderflow_row.addWidget(value)
            orderflow_row.addSpacing(4)
        orderflow_row.addStretch()
        fields["open_pos"] = self.label_factory("Pos 0", self.theme["dim"], 10, True)
        orderflow_row.addWidget(fields["open_pos"])
        groups["_grp_of"] = self._wrap(sections["_sec_of"], orderflow_row, self.separator_factory())
        body_layout.addWidget(groups["_grp_of"])

        sections["_sec_net"] = self.section_factory(texts["sec_network"])
        network_row = QHBoxLayout()
        network_row.setSpacing(4)
        network_row.setContentsMargins(0, 0, 0, 0)
        network_labels: dict[str, Any] = {}
        network_dots: dict[str, Any] = {}
        for name in ["Trinity", "Kraken", "Sound"]:
            dot = self.label_factory("●", self.theme["dim"], 10)
            dot.setFixedWidth(12)
            network_row.addWidget(dot)
            label = self.label_factory(f"{name} —", self.theme["dim"], 10)
            network_labels[name] = label
            network_dots[name] = dot
            network_row.addWidget(label)
            network_row.addSpacing(4)
        network_row.addStretch()
        fields["ticks"] = self.label_factory("Ticks 0", self.theme["dim"], 10)
        fields["errors"] = self.label_factory("Errors 0", self.theme["dim"], 10)
        network_row.addWidget(fields["ticks"])
        network_row.addWidget(fields["errors"])

        llm_network_row = QHBoxLayout()
        llm_network_row.setSpacing(2)
        llm_network_row.setContentsMargins(0, 0, 0, 0)
        llm_network_row.addWidget(self.label_factory("LLM", self.theme["dim"], 9, mono=False))
        llm_network_row.addSpacing(4)
        llm_network_dots: list[Any] = []
        for _ in range(12):
            dot = self.label_factory("●", self.theme["dim"], 9)
            dot.setFixedWidth(11)
            llm_network_row.addWidget(dot)
            llm_network_dots.append(dot)
        llm_network_row.addStretch()
        fields["phase"] = self.label_factory("Phase —", self.theme["dim"], 10)
        fields["edge"] = self.label_factory("Edge —", self.theme["dim"], 10)
        llm_network_row.addWidget(fields["phase"])
        llm_network_row.addWidget(fields["edge"])
        groups["_grp_net"] = self._wrap(sections["_sec_net"], network_row, llm_network_row, self.separator_factory())
        body_layout.addWidget(groups["_grp_net"])

        sections["_sec_perf"] = self.section_factory(texts["sec_perf"])
        performance_top = QHBoxLayout()
        performance_top.setSpacing(8)
        performance_top.setContentsMargins(0, 0, 0, 0)
        fields["roi_gauge"] = self.roi_gauge_factory()
        performance_top.addWidget(fields["roi_gauge"])

        performance_stack = QVBoxLayout()
        performance_stack.setSpacing(5)
        performance_stack.setContentsMargins(0, 0, 0, 0)

        perf_headline = QHBoxLayout()
        perf_headline.setSpacing(8)
        perf_headline.setContentsMargins(0, 0, 0, 0)
        fields["pf_Sharpe"] = self.label_factory("ROI +0.00%", self.theme["text2"], 13, True)
        fields["pf_WinRate"] = self.label_factory("WR —", self.theme["dim2"], 11, True)
        fields["pf_Trades"] = self.label_factory("Trades 0", self.theme["dim"], 11, True)
        perf_headline.addWidget(fields["pf_Sharpe"])
        perf_headline.addWidget(fields["pf_WinRate"])
        perf_headline.addWidget(fields["pf_Trades"])
        perf_headline.addStretch()
        performance_stack.addLayout(perf_headline)

        fields["roi_bar"] = self.roi_bar_factory()
        performance_stack.addWidget(fields["roi_bar"])

        perf_finance = QHBoxLayout()
        perf_finance.setSpacing(6)
        perf_finance.setContentsMargins(0, 0, 0, 0)
        fields["pf_profit"] = self.label_factory("Profit $0.00", self.theme["text2"], 11, True)
        fields["pf_loss"] = self.label_factory("Loss $0.00", self.theme["sell"], 11, True)
        fields["pf_PF"] = self.label_factory("Net $0.00", self.theme["dim"], 11, True)
        perf_finance.addWidget(fields["pf_profit"])
        perf_finance.addWidget(fields["pf_loss"])
        perf_finance.addWidget(fields["pf_PF"])
        perf_finance.addStretch()
        performance_stack.addLayout(perf_finance)

        performance_row_2 = QHBoxLayout()
        performance_row_2.setSpacing(8)
        performance_row_2.setContentsMargins(0, 0, 0, 0)
        fields["tp_hits"] = self.label_factory("TP 0", self.theme["buy"], 10, True)
        fields["sl_hits"] = self.label_factory("SL 0", self.theme["sell"], 10, True)
        fields["pf_edge"] = self.label_factory("Sharpe —", self.theme["dim"], 10, True)
        performance_row_2.addWidget(fields["tp_hits"])
        performance_row_2.addWidget(fields["sl_hits"])
        performance_row_2.addWidget(fields["pf_edge"])
        performance_row_2.addStretch()
        fields["today"] = self.label_factory("Today: $0.00", self.theme["dim"], 13, True)
        performance_row_2.addWidget(fields["today"])
        performance_stack.addLayout(performance_row_2)
        performance_top.addLayout(performance_stack, 1)
        groups["_grp_perf"] = self._wrap(sections["_sec_perf"], performance_top)
        body_layout.addWidget(groups["_grp_perf"])

        sections["_sec_sound"] = self.section_factory(texts["sec_sound"])
        sound_row_1 = QHBoxLayout()
        sound_row_1.setSpacing(6)
        sound_row_1.setContentsMargins(0, 0, 0, 0)
        fields["sound_voice"] = self.label_factory("VOICE —", self.theme["accent"], 10, True)
        fields["sound_persona"] = self.label_factory("CC —", self.theme["dim2"], 9, False)
        sound_row_1.addWidget(fields["sound_voice"])
        sound_row_1.addWidget(fields["sound_persona"], 1)

        fields["sound_sample"] = self.label_factory('>> "—"', self.theme["text2"], 10, False)
        fields["sound_sample"].setWordWrap(True)
        groups["_grp_sound"] = self._wrap(sections["_sec_sound"], sound_row_1, fields["sound_sample"], self.separator_factory())
        body_layout.addWidget(groups["_grp_sound"])

        body_layout.addSpacing(4)
        footer = QLabel(footer_text)
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(
            f"color:{self.theme['dim']};font-size:8px;background:transparent;letter-spacing:1px;"
        )
        body_layout.addWidget(footer)
        body_layout.addStretch()

        return DashboardBodyRefs(
            status_label=status_label,
            sentiment_label=sentiment_label,
            symbol_label=symbol_label,
            chart=chart,
            gauge=gauge,
            fields=fields,
            llm_widgets=llm_widgets,
            network_labels=network_labels,
            network_dots=network_dots,
            llm_network_dots=llm_network_dots,
            sections=sections,
            groups=groups,
        )
