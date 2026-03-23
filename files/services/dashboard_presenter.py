from __future__ import annotations

from typing import Any


class DashboardPresenter:
	def __init__(
		self,
		*,
		theme: dict[str, str],
		font_family: str,
		status_label: Any,
		sentiment_label: Any,
		fields: dict[str, Any],
		llm_widgets: dict[str, dict[str, Any]],
		network_labels: dict[str, Any],
		network_dots: dict[str, Any],
		llm_network_dots: list[Any],
		sections: dict[str, Any],
		groups: dict[str, Any],
		chart: Any,
		gauge: Any,
		start_button: Any,
		profit_button: Any,
		algo_button: Any,
		stop_button: Any,
	):
		self.theme = theme
		self.font_family = font_family
		self.status_label = status_label
		self.sentiment_label = sentiment_label
		self.fields = fields
		self.llm_widgets = llm_widgets
		self.network_labels = network_labels
		self.network_dots = network_dots
		self.llm_network_dots = llm_network_dots
		self.sections = sections
		self.groups = groups
		self.chart = chart
		self.gauge = gauge
		self.start_button = start_button
		self.profit_button = profit_button
		self.algo_button = algo_button
		self.stop_button = stop_button

	def _theme_color(self, color_key: str, fallback: str = "dim") -> str:
		return self.theme.get(color_key, self.theme.get(fallback, self.theme["dim"]))

	def _label_style(self, color_key: str, size: int, *, bold: bool = False, fallback: str = "dim") -> str:
		weight = "700" if bold else "500"
		return (
			f"color:{self._theme_color(color_key, fallback)};"
			f"font-size:{size}px;font-family:{self.font_family};"
			f"font-weight:{weight};background:transparent;"
		)

	def _progress_style(self, chunk_color: str, *, background_key: str = "card", radius: int = 2) -> str:
		return (
			f"QProgressBar{{background:{self.theme[background_key]};border:none;border-radius:{radius}px;}}"
			f"QProgressBar::chunk{{background:{chunk_color};border-radius:{radius}px;}}"
		)

	def _set_llm_strip(self, running: bool, decision: str):
		state = decision[:1] if running and decision in {"BUY", "SELL", "HOLD"} else "—"
		color = {"BUY": self.theme["buy"], "SELL": self.theme["sell"], "HOLD": self.theme["hold"]}.get(decision, self.theme["dim"])
		if not running:
			color = self.theme["dim"]
		for item in self.llm_widgets.values():
			item["dot"].setStyleSheet(
				f"color:{color};font-size:12px;font-weight:700;background:transparent;"
			)
			item["state"].setText(state)
			item["state"].setStyleSheet(
				f"color:{color};font-size:11px;font-weight:700;background:transparent;font-family:{self.font_family};"
			)

	def _apply_header_vm(self, vm: dict):
		header = vm["header"]
		self.status_label.setText(header["status_text"])
		self.sentiment_label.setText(header["sentiment_text"])
		self.sentiment_label.setStyleSheet(
			self._label_style(header["sentiment_color"], 10, bold=True, fallback="dim2")
		)
		self._set_llm_strip(header["llm_strip_running"], header["llm_strip_action"])

	def _apply_consensus_vm(self, vm: dict):
		consensus = vm["consensus"]
		cons_color = self._theme_color(consensus["color"], "hold")
		self.fields["consensus"].setText(consensus["label"])
		self.fields["consensus"].setStyleSheet(
			f"color:{cons_color};font-size:10px;font-weight:700;font-family:{self.font_family};background:transparent;"
		)
		self.fields["cons_pct"].setText(consensus["pct_text"])
		self.fields["cons_bar"].setValue(consensus["bar_value"])
		self.fields["cons_bar"].setStyleSheet(self._progress_style(cons_color))
		self.fields["timing"].setText(consensus["timing_text"])
		self.fields["rr"].setText(consensus["rr_text"])

	def _apply_market_vm(self, vm: dict):
		market = vm["market"]
		indicators = vm["indicators"]
		ml = vm["ml"]
		patterns = vm["patterns"]

		self.fields["Bid"].setText(market["bid_text"])
		if market["bid_value"] > 0:
			try:
				self.chart.add_price(market["bid_value"])
			except Exception:
				pass
		self.fields["Ask"].setText(market["ask_text"])
		self.fields["Spread"].setText(market["spread_text"])
		self.fields["Session"].setText(market["session_text"])
		self.fields["Regime"].setText(market["regime_text"])

		self.fields["RSI"].setText(indicators["rsi_text"])
		self.fields["ADX"].setText(indicators["adx_text"])
		self.fields["MACD"].setText(indicators["macd_text"])
		self.fields["ATR"].setText(indicators["atr_text"])
		self.fields["Stoch"].setText(indicators["stoch_text"])
		self.fields["BB W"].setText(indicators["bbw_text"])
		rsi_color = self._theme_color(indicators["rsi_color"], "warn")
		self.fields["RSI"].setStyleSheet(
			f"color:{rsi_color};font-size:12px;font-family:{self.font_family};font-weight:500;background:transparent;"
		)
		self.fields["rsi_bar"].setValue(indicators["rsi_value"])
		self.fields["rsi_bar"].setStyleSheet(self._progress_style(rsi_color))

		self.fields["ml_DNN"].setText(ml["dnn_text"])
		self.fields["ml_LSTM"].setText(ml["lstm_text"])
		self.fields["ml_RL"].setText(ml["rl_text"])
		self.fields["ml_Bayesian"].setText(ml["bayesian_text"])
		self.fields["ml_pred"].setText(ml["pred_text"])
		self.fields["bull"].setText(ml["bull_text"])
		self.fields["bear"].setText(ml["bear_text"])
		self.fields["bull_bar"].setValue(ml["bull_bar_value"])
		self.fields["bull_bar"].setStyleSheet(
			f"QProgressBar{{background:{self.theme['sell']}55;border:none;border-radius:2px;}}"
			f"QProgressBar::chunk{{background:{self.theme['buy']};border-radius:2px;}}"
		)

		self.fields["pat"].setText(patterns["pattern_text"])
		self.fields["pat_b"].setText(patterns["bull_text"])
		self.fields["pat_r"].setText(patterns["bear_text"])
		self.fields["quality"].setText(patterns["quality_text"])

	def _apply_llm_votes_vm(self, vm: dict):
		for item in vm["llm_votes"]:
			name = item["name"]
			if name not in self.llm_widgets:
				continue
			self.llm_widgets[name]["dot"].setText(item["dot_char"])
			self.llm_widgets[name]["dot"].setStyleSheet(
				f"color:{self._theme_color(item['dot_color'])};font-size:12px;font-weight:700;background:transparent;"
			)
			self.llm_widgets[name]["state"].setText(item["state_text"])
			self.llm_widgets[name]["state"].setStyleSheet(
				f"color:{self._theme_color(item['state_color'])};font-size:9px;font-weight:700;background:transparent;font-family:{self.font_family};"
			)

	def _apply_attack_vm(self, vm: dict):
		attack = vm["attack"]
		attack_color = self._theme_color(attack["icon_color"])
		dir_color = self._theme_color(attack["dir_color"])
		cool_color = self._theme_color(attack["cool_color"], "warn")

		self.fields["atk_icon"].setText(attack["icon_text"])
		self.fields["atk_icon"].setStyleSheet(
			f"color:{attack_color};font-size:11px;font-family:{self.font_family};font-weight:700;background:transparent;"
		)
		self.fields["atk_pct_lbl"].setText(attack["pct_text"])
		self.fields["atk_pct_lbl"].setStyleSheet(
			f"color:{self._theme_color(attack['pct_color'])};font-size:12px;font-family:{self.font_family};font-weight:700;background:transparent;"
		)
		self.fields["atk_dir"].setText(attack["dir_text"])
		self.fields["atk_dir"].setStyleSheet(
			f"color:{dir_color};font-size:11px;font-family:{self.font_family};background:transparent;"
		)
		self.fields["atk_cool"].setText(attack["cool_text"])
		self.fields["atk_cool"].setStyleSheet(
			f"color:{cool_color};font-size:11px;font-family:{self.font_family};font-weight:700;background:transparent;"
		)
		self.fields["atk_cool"].setToolTip(attack["tooltip"])
		self.fields["atk_bar"].setValue(attack["pct_value"])
		self.fields["atk_bar"].setStyleSheet(self._progress_style(attack_color, radius=3))
		try:
			self.gauge.set_value(attack["gauge_value"], attack["gauge_direction"])
		except Exception:
			pass

	def _apply_network_vm(self, vm: dict):
		orderflow = vm["orderflow"]
		network = vm["network"]

		self.fields["of_Buy"].setText(orderflow["buy_text"])
		self.fields["of_Sell"].setText(orderflow["sell_text"])
		self.fields["of_Delta"].setText(orderflow["delta_text"])
		self.fields["of_Imbalance"].setText(orderflow["imbalance_text"])
		self.fields["of_CVD"].setText(orderflow["cvd_text"])
		self.fields["open_pos"].setText(orderflow["open_pos_text"])
		self.fields["open_pos"].setStyleSheet(
			self._label_style(orderflow["open_pos_color"], 10, bold=True)
		)

		for comp, color_key in network["component_colors"].items():
			if comp in self.network_dots:
				self.network_dots[comp].setStyleSheet(
					f"color:{self._theme_color(color_key)};font-size:11px;background:transparent;"
				)
		self.network_labels["Trinity"].setText(network["trinity_text"])
		self.network_labels["Kraken"].setText(network["kraken_text"])
		self.network_labels["Sound"].setText(network["sound_text"])
		self.fields["ticks"].setText(network["ticks_text"])
		self.fields["errors"].setText(network["errors_text"])

		for i, color_key in enumerate(network["llm_colors"]):
			if i < len(self.llm_network_dots):
				self.llm_network_dots[i].setStyleSheet(
					f"color:{self._theme_color(color_key)};font-size:9px;background:transparent;"
				)

	def _apply_performance_vm(self, vm: dict):
		memoria = vm["memoria"]
		performance = vm["performance"]
		sound = vm["sound"]

		self.fields["phase"].setText(memoria["phase_text"])
		self.fields["edge"].setText(memoria["edge_text"])
		self.fields["edge"].setStyleSheet(
			self._label_style(memoria["edge_color"], 12)
		)

		self.fields["pf_WinRate"].setText(performance["winrate_text"])
		self.fields["pf_WinRate"].setStyleSheet(
			self._label_style(performance["winrate_color"], 11, bold=True, fallback="sell")
		)
		self.fields["pf_PF"].setText(performance["pf_text"])
		self.fields["pf_Sharpe"].setText(performance["sharpe_text"])
		self.fields["pf_Trades"].setText(performance["trades_text"])
		self.fields["pf_profit"].setText(performance["profit_text"])
		self.fields["pf_profit"].setStyleSheet(self._label_style(performance["profit_color"], 11, bold=True, fallback="text2"))
		self.fields["pf_loss"].setText(performance["loss_text"])
		self.fields["pf_loss"].setStyleSheet(self._label_style(performance["loss_color"], 11, bold=True, fallback="sell"))
		self.fields["pf_edge"].setText(performance["edge_sharpe_text"])
		self.fields["pf_edge"].setStyleSheet(self._label_style(memoria["edge_color"], 10, bold=True))
		self.fields["tp_hits"].setText(performance["tp_hits_text"])
		self.fields["tp_hits"].setStyleSheet(
			self._label_style(performance["tp_hits_color"], 10, bold=True)
		)
		self.fields["sl_hits"].setText(performance["sl_hits_text"])
		self.fields["sl_hits"].setStyleSheet(
			self._label_style(performance["sl_hits_color"], 10, bold=True)
		)
		self.fields["today"].setText(performance["today_text"])
		self.fields["today"].setStyleSheet(
			self._label_style(performance["today_color"], 10)
		)
		try:
			self.fields["roi_gauge"].set_metrics(performance["roi_value"], performance["winrate_text"], performance["trades_text"])
		except Exception:
			pass
		try:
			self.fields["roi_bar"].set_metrics(performance["roi_value"], performance["roi_band"], performance["roi_color"])
		except Exception:
			pass
		self.fields["sound_voice"].setText(f"VOICE {sound['voice_text']}")
		self.fields["sound_persona"].setText(sound["persona_text"])
		self.fields["sound_sample"].setText(f'>> "{sound["sample_text"]}"')

	def _apply_button_vm(self, vm: dict):
		buttons = vm["buttons"]
		self.start_button.setEnabled(buttons["start_enabled"])
		self.stop_button.setEnabled(buttons["stop_enabled"])
		if self.algo_button is not None:
			self.algo_button.setText(buttons["algo_text"])
			self.algo_button.setToolTip(buttons["algo_tooltip"])
			self.algo_button.mode = "secondary" if "ON" in buttons["algo_text"] else "danger"
			self.algo_button.update()

		start_state = buttons["start_state"]
		if start_state == "running":
			self.start_button.set_running(True)
		elif start_state == "waiting_ea":
			self.start_button.set_waiting_ea()
		elif start_state == "idle":
			self.start_button.set_running(False)

		if buttons["reset_stop"]:
			self.stop_button.reset_to_danger()

	def update_profit_button_text(self, width: int, texts: dict):
		full = texts["close_profit"]
		short = texts.get("close_profit_short", full)
		mini = texts.get("close_profit_mini", short)
		if width >= 460:
			text = full
		elif width >= 360:
			text = short
		else:
			text = mini
		if self.profit_button is None:
			return
		self.profit_button.setText(text)
		self.profit_button.setToolTip(full)
		self.profit_button.setMinimumWidth(56 if width < 360 else 70)
		self.profit_button.setMaximumWidth(170 if width < 460 else 220)

	def apply_responsive(self, width: int, height: int, texts: dict):
		ultra = width < 260 or height < 200
		for group in self.groups.values():
			if group:
				group.setVisible(True)
		if self.chart:
			self.chart.setVisible(width >= 200)
		self.update_profit_button_text(width, texts)
		btn_h = 24 if ultra else 34
		for btn in (self.start_button, self.stop_button, self.profit_button, self.algo_button):
			if btn:
				btn.setFixedHeight(btn_h)

	def apply_language(self, lang: str, texts: dict, width: int):
		self.start_button.set_lang_texts(texts)
		self.stop_button.set_lang_texts(texts)
		if self.profit_button:
			self.profit_button.set_lang_texts(texts)
		if self.algo_button:
			self.algo_button.set_lang_texts(texts)

		self.start_button._orig_text = texts["start"]
		self.stop_button._orig_text = texts["stop"]
		if self.profit_button:
			self.profit_button._orig_text = texts["close_profit"]
		if self.algo_button:
			self.algo_button._orig_text = texts["algo_off"]

		if not self.start_button._running and not self.start_button._launching and not self.start_button._waiting_ea:
			self.start_button.setText(texts["start"])
		elif self.start_button._waiting_ea:
			self.start_button._text = texts["waiting_ea"]
			self.start_button.update()
		elif self.start_button._running:
			self.start_button._text = texts["injected"]
			self.start_button.update()

		if not self.stop_button._stopping and not self.stop_button._stopped:
			self.stop_button.setText(texts["stop"])
		elif self.stop_button._stopped:
			self.stop_button._text = texts["stopped"]
			self.stop_button.update()

		self.update_profit_button_text(width, texts)
		for key, sec_key in [("sec_market", "_sec_market"), ("sec_indicators", "_sec_ind"),
							("sec_ml", "_sec_ml"), ("sec_brain", "_sec_brain"),
							("sec_patterns", "_sec_pat"), ("sec_attack", "_sec_atk"),
							("sec_orderflow", "_sec_of"), ("sec_network", "_sec_net"),
							("sec_perf", "_sec_perf"), ("sec_sound", "_sec_sound")]:
			section = self.sections.get(sec_key)
			if section:
				label = section.findChild(type(self.status_label))
				if label:
					label.setText(texts.get(key, label.text()))

	def apply_dashboard_vm(self, vm: dict):
		self._apply_header_vm(vm)
		self._apply_consensus_vm(vm)
		self._apply_market_vm(vm)
		self._apply_llm_votes_vm(vm)
		self._apply_attack_vm(vm)
		self._apply_network_vm(vm)
		self._apply_performance_vm(vm)
		self._apply_button_vm(vm)
