from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .mt5_service import MT5Service
from .runtime_manager import RuntimeManager


class TelemetryService:
    def __init__(self, runtime_manager: RuntimeManager, mt5_service: MT5Service | None = None):
        self.runtime_manager = runtime_manager
        self.mt5_service = mt5_service
        self._sound_cache: dict[str, dict] = {}

    @staticmethod
    def _as_int(value: Any, default: int = 0) -> int:
        try:
            return int(value or 0)
        except Exception:
            return default

    @staticmethod
    def _as_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value or 0.0)
        except Exception:
            return default

    @staticmethod
    def _format_price(value: Any) -> str:
        try:
            numeric = float(value)
        except Exception:
            return "—"
        return f"{numeric:.5f}" if numeric > 0 else "—"

    @staticmethod
    def _format_float(value: Any, digits: int = 1) -> str:
        if value in (None, 0, 0.0, ""):
            return "—"
        try:
            return f"{float(value):.{digits}f}"
        except Exception:
            return "—"

    @staticmethod
    def _clip(value: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, value))

    def _load_sound_profile(self, pair_dir: str | Path | None, prefix: str | None, sym: str) -> dict:
        if not pair_dir or not prefix:
            return {"voice": "—", "persona": "No sound profile", "phrases": {}, "sample": "—"}

        sound_path = Path(pair_dir) / f"{prefix}sound.py"
        cache_key = str(sound_path).lower()
        cached = self._sound_cache.get(cache_key)
        if cached is not None:
            return cached

        profile = {"voice": "—", "persona": f"{sym} sound engine", "phrases": {}, "sample": "—"}
        if not sound_path.exists():
            self._sound_cache[cache_key] = profile
            return profile

        try:
            raw = sound_path.read_text(encoding="utf-8", errors="ignore")
            for line in raw.splitlines()[:24]:
                stripped = line.strip("# ║ ")
                if "Premium Female Voice:" in stripped:
                    profile["persona"] = stripped
                elif "Trading Phrases" in stripped:
                    profile["persona"] = stripped

            tree = ast.parse(raw)
            for node in tree.body:
                if not isinstance(node, ast.Assign):
                    continue
                for target in node.targets:
                    if not isinstance(target, ast.Name):
                        continue
                    if target.id == "VOICE":
                        try:
                            profile["voice"] = str(ast.literal_eval(node.value))
                        except Exception:
                            pass
                    elif target.id == "PHRASES":
                        try:
                            phrases = ast.literal_eval(node.value)
                            if isinstance(phrases, dict):
                                normalized = {}
                                for key, value in phrases.items():
                                    items = value if isinstance(value, list) else []
                                    normalized[str(key).upper()] = [str(item) for item in items if isinstance(item, str)]
                                profile["phrases"] = normalized
                        except Exception:
                            pass

            phrase_pool = profile["phrases"].get("BUY") or profile["phrases"].get("SELL") or profile["phrases"].get("HOLD") or []
            if phrase_pool:
                profile["sample"] = phrase_pool[0]
        except Exception:
            pass

        self._sound_cache[cache_key] = profile
        return profile

    def _roi_color_key(self, roi_pct: float) -> str:
        if roi_pct < -0.75:
            return "error"
        if roi_pct < 0:
            return "warn"
        if roi_pct < 1.0:
            return "buy"
        return "violet"

    def _roi_band_text(self, roi_pct: float) -> str:
        if roi_pct < -0.75:
            return "Drawdown"
        if roi_pct < 0:
            return "Soft Loss"
        if roi_pct < 1.0:
            return "Green Day"
        return "Purple Run"

    def _status_text(self, texts: dict, supported: bool, running: bool, stats: dict, stats_age: float | None, process_count: int, genomes: int, ticks: int) -> str:
        if not supported:
            return texts["no_launcher"]
        if running:
            uptime_start = self._as_float(stats.get("uptime"), 0.0)
            uptime_secs = max(0, int(datetime.now(timezone.utc).timestamp() - uptime_start)) if uptime_start else 0
            hh = uptime_secs // 3600
            mm = (uptime_secs % 3600) // 60
            ss = uptime_secs % 60
            proc_txt = f"  •  Proc {process_count}" if process_count else ""
            return f"{texts['live']} • Up {hh:02d}:{mm:02d}:{ss:02d}  •  Genomes {genomes}  •  Ticks {ticks}{proc_txt}"
        if stats_age is not None:
            return texts["offline_last"].format(age=int(stats_age)) + f"  •  Ticks {ticks}"
        return texts["offline_none"]

    def _start_button_state(
        self,
        current: dict,
        running: bool,
        executor_alive: bool,
        stats_age: float | None,
        stats_fresh: bool,
        stats: dict,
        ticks: int,
        genomes: int,
    ) -> str | None:
        quimera_flag = bool(stats.get("quimera_connected", False) or stats.get("quimera_handshakes", 0) > 0)
        strict_stats_fresh = bool(stats_fresh and stats_age is not None and stats_age < 15)
        ea_connected = quimera_flag and (executor_alive or strict_stats_fresh)
        really_running = (running and strict_stats_fresh) or executor_alive
        warmup_done = ticks > 0 or genomes > 0
        launching = bool(current.get("launching"))
        waiting_ea = bool(current.get("waiting_ea"))
        current_running = bool(current.get("running"))

        if launching:
            if not running:
                return "idle"
            if really_running and warmup_done and ea_connected:
                return "running"
            if really_running and warmup_done:
                return "waiting_ea"
            return None
        if really_running and ea_connected:
            return "running"
        if really_running and not ea_connected:
            return "waiting_ea"
        if running and not strict_stats_fresh:
            return "waiting_ea"
        if not running and (current_running or waiting_ea or launching):
            return "idle"
        return None

    def collect_snapshot(self, sym: str, runtime: dict) -> dict:
        payload = self.runtime_manager.collect_pair_snapshot(sym, runtime)
        if self.mt5_service is not None:
            payload["mt5_day"] = self.mt5_service.get_day_metrics(sym).to_dict()
        pair_dir = payload.get("pair_dir")
        payload["sound_profile"] = self._load_sound_profile(pair_dir, runtime.get("prefix"), sym)
        return payload

    def current_session(self) -> str:
        hour = datetime.now(timezone.utc).hour
        if 0 <= hour < 7:
            return "TOKYO"
        if 7 <= hour < 12:
            return "LONDON"
        if 12 <= hour < 21:
            return "NY/LONDON"
        return "SYDNEY"

    def derive_runtime_view(self, data: dict) -> dict:
        runtime_state = data.get("runtime_state", {}) if isinstance(data.get("runtime_state"), dict) else {}
        stats = data.get("stats", {}) if isinstance(data.get("stats"), dict) else {}
        stats_age = data.get("stats_age")
        tcp = data.get("tcp", {}) if isinstance(data.get("tcp"), dict) else {}
        live_pid = runtime_state.get("live_pid", data.get("live_pid"))
        supported = runtime_state.get("supported")
        executor_alive = runtime_state.get("executor_alive")
        if executor_alive is None:
            executor_alive = tcp.get("executor", False) if isinstance(tcp, dict) else False
        stats_fresh = runtime_state.get("stats_fresh")
        if stats_fresh is None:
            stats_fresh = stats_age is not None and stats_age <= 20
        running = runtime_state.get("running")
        if running is None:
            running = live_pid is not None or stats_fresh or executor_alive
        action = str(stats.get("last_action") or stats.get("current_direction") or "HOLD").upper()
        if action not in {"BUY", "SELL", "HOLD"}:
            action = "HOLD"
        return {
            "runtime_state": runtime_state,
            "stats": stats,
            "stats_age": stats_age,
            "tcp": tcp,
            "live_pid": live_pid,
            "supported": supported,
            "executor_alive": executor_alive,
            "stats_fresh": bool(stats_fresh),
            "running": bool(running),
            "action": action,
            "session": self.current_session(),
            "process_count": int(runtime_state.get("process_count") or 0),
        }

    def build_dashboard_vm(
        self,
        data: dict,
        texts: dict,
        llm_names: list[str],
        launcher_available: bool,
        button_state: dict,
    ) -> dict:
        view = self.derive_runtime_view(data)
        stats = view["stats"]
        stats_age = view["stats_age"]
        memoria = data.get("memoria", {}) if isinstance(data.get("memoria"), dict) else {}
        tcp = view["tcp"]
        tcp_llm = data.get("tcp_llm", []) if isinstance(data.get("tcp_llm"), list) else []

        supported = view["supported"]
        if supported is None:
            supported = bool(launcher_available)

        running = bool(view["running"])
        executor_alive = bool(view["executor_alive"])
        stats_fresh = bool(view["stats_fresh"])
        action = view["action"]
        process_count = self._as_int(view.get("process_count"), 0)

        genomes = self._as_int(stats.get("genome_counter") or stats.get("genomes_received"), 0)
        ticks = self._as_int(stats.get("ticks_processed"), 0)
        errors = self._as_int(stats.get("errors"), 0)
        wins = self._as_int(stats.get("wins"), 0)
        losses = self._as_int(stats.get("losses"), 0)
        trades = wins + losses
        winrate = stats.get("winrate")
        pnl_today = self._as_float(stats.get("pnl_today") or stats.get("today_pnl"), 0.0)
        day_metrics = data.get("mt5_day", {}) if isinstance(data.get("mt5_day"), dict) else {}
        if day_metrics.get("ok"):
            wins = self._as_int(day_metrics.get("wins"), wins)
            losses = self._as_int(day_metrics.get("losses"), losses)
            trades = self._as_int(day_metrics.get("trades"), trades)
            winrate = day_metrics.get("winrate", winrate)
            pnl_today = self._as_float(day_metrics.get("net_profit"), pnl_today)
        gross_profit = self._as_float(day_metrics.get("gross_profit"), max(0.0, pnl_today))
        gross_loss = self._as_float(day_metrics.get("gross_loss"), abs(min(0.0, pnl_today)))
        roi_pct = self._as_float(day_metrics.get("roi_pct"), 0.0)
        algo_enabled = bool(day_metrics.get("algo_enabled", False))
        trinity_pings = self._as_int(stats.get("trinity_pings"), 0)
        trinity_acks = self._as_int(stats.get("trinity_acks", stats.get("trinity_responses", 0)), 0)
        kraken_pings = self._as_int(stats.get("kraken_pings"), 0)
        kraken_acks = self._as_int(stats.get("kraken_acks"), 0)
        trinity_pct = int(round((trinity_acks / trinity_pings) * 100)) if trinity_pings else 0

        sentiment_icon, sentiment_text, sentiment_color = {
            "BUY": ("▲", "BULLISH", "buy"),
            "SELL": ("▼", "BEARISH", "sell"),
        }.get(action, ("◆", "NEUTRAL", "dim2"))

        cons_color = {"BUY": "buy", "SELL": "sell"}.get(action, "hold")
        cons_buy_pct = self._as_int(stats.get("consensus_buy_pct"), 0)
        cons_sell_pct = self._as_int(stats.get("consensus_sell_pct"), 0)
        llm_agreement = self._as_float(stats.get("llm_agreement"), 0.0)
        agree_pct = int(round(llm_agreement * 100)) if llm_agreement > 0 else (
            cons_buy_pct if action == "BUY" else (cons_sell_pct if action == "SELL" else 0)
        )

        llm7_quality = self._as_int(stats.get("llm7_quality"), 0)
        llm8_timing = self._as_float(stats.get("llm8_timing", 1.0), 1.0)
        llm9_rr = self._as_float(stats.get("llm9_rr"), 0.0)

        bid_value = stats.get("market_bid")
        ask_value = stats.get("market_ask")
        spread_value = stats.get("market_spread")
        session_value = stats.get("market_session") or view["session"]
        trend_value = str(stats.get("market_trend", "") or "")

        rsi_value = self._as_float(stats.get("ind_rsi"), 50.0)
        adx_value = self._as_float(stats.get("ind_adx"), 0.0)
        rsi_color = "sell" if rsi_value > 70 else ("buy" if rsi_value < 30 else "warn")

        dnn_value = self._as_float(stats.get("ml_dnn"), 0.0)
        lstm_value = self._as_float(stats.get("ml_lstm"), 0.0)
        rl_value = str(stats.get("ml_rl", "HOLD") or "HOLD")
        bull_value = self._as_float(stats.get("ml_bull"), 0.5)
        bear_value = self._as_float(stats.get("ml_bear"), 0.5)
        bay_pct = int(round((bull_value + (1.0 - bear_value)) / 2.0 * 100))
        bull_pct = int(round(bull_value * 100))

        pattern_bull = self._as_int(stats.get("pattern_bull"), 0)
        pattern_bear = self._as_int(stats.get("pattern_bear"), 0)
        pattern_quality = self._as_int(stats.get("pattern_quality"), llm7_quality)
        pattern_text = str(stats.get("patterns_text", "") or "")
        if pattern_text.startswith("["):
            pattern_text = ""

        llm_votes = []
        for name in llm_names:
            vote = stats.get(f"llm_{name}")
            confidence = self._as_int(stats.get(f"llm_{name}_conf"), 0)
            status = str(stats.get(f"llm_{name}_status", "") or "")
            if status == "ONLINE":
                dot_color = {"BUY": "buy", "SELL": "sell"}.get(vote, "hold")
                dot_char = "●"
            elif status in {"IDLE", "WAITING", "PENDING"}:
                dot_color = "warn"
                dot_char = "◐"
            elif status == "OFFLINE":
                dot_color = "error"
                dot_char = "○"
            elif vote in {"BUY", "SELL", "HOLD"}:
                dot_color = {"BUY": "buy", "SELL": "sell"}.get(vote, "hold")
                dot_char = "●"
            elif running:
                dot_color = "warn"
                dot_char = "◐"
            else:
                dot_color = "dim"
                dot_char = "○"

            if vote in {"BUY", "SELL", "HOLD"}:
                state_color = {"BUY": "buy", "SELL": "sell"}.get(vote, "dim2")
                short_vote = {"BUY": "BUY", "SELL": "SEL", "HOLD": "HLD"}.get(vote, str(vote)[:3])
                state_text = f"{short_vote}{confidence}" if confidence else short_vote
            elif running:
                state_color = {"BUY": "buy", "SELL": "sell"}.get(action, "hold")
                state_text = action[:3]
            else:
                state_color = "dim"
                state_text = "─"

            llm_votes.append({
                "name": name,
                "dot_char": dot_char,
                "dot_color": dot_color,
                "state_text": state_text[:6],
                "state_color": state_color,
            })

        attack_pct = self._as_float(stats.get("attack_pct"), 0.0)
        attack_dir = str(stats.get("attack_dir", "NONE") or "NONE").upper()
        attack_cooldown = self._as_float(stats.get("attack_countdown"), 0.0)
        if attack_pct >= 80:
            attack_icon = "🚀 LAUNCH"
            attack_color = "buy"
        elif attack_pct >= 60:
            attack_icon = "⚡ READY "
            attack_color = "buy"
        elif attack_pct >= 40:
            attack_icon = "◐ WAIT  "
            attack_color = "warn"
        else:
            attack_icon = "○ IDLE  "
            attack_color = "dim"
        attack_dir_color = {"BUY": "buy", "SELL": "sell"}.get(attack_dir, "dim")

        news_bias = str(stats.get("news_bias", "NEUTRAL") or "NEUTRAL")
        news_conf = self._as_float(stats.get("news_conf"), 0.0)
        whale_conf = self._as_float(stats.get("whale_conf"), 0.0)
        sweep_type = str(stats.get("sweep_type", "NONE") or "NONE")
        attack_cool_text = f"CD {attack_cooldown:.1f}s"
        attack_cool_color = "warn"
        if whale_conf >= 60 or sweep_type not in {"NONE", ""}:
            attack_cool_text = f"🐋{whale_conf:.0f}%"
            attack_cool_color = "buy"
        attack_tooltip_icon = {"BULLISH": "📈", "BEARISH": "📉"}.get(news_bias, "📊")

        open_positions = self._as_int(stats.get("open_positions"), 0)
        tcp_colors = {
            component: ("success" if alive else ("error" if alive is False else "dim"))
            for component, alive in tcp.items()
        }
        llm_tcp_colors = [
            "success" if alive else ("error" if alive is False else "dim")
            for alive in tcp_llm
        ]

        edge_monitor = memoria.get("edge_monitor", {}) if isinstance(memoria.get("edge_monitor"), dict) else {}
        edge_status = edge_monitor.get("edge_status", "—")
        sharpe_value = edge_monitor.get("rolling_sharpe_50", 0)
        edge_color = {"POSITIVE": "success", "NEGATIVE": "error", "UNKNOWN": "warn"}.get(edge_status, "dim")

        tp_hits = self._as_int(stats.get("tp_hits"), 0)
        sl_hits = self._as_int(stats.get("sl_hits"), 0)
        pnl_sign = "+" if pnl_today >= 0 else ""
        start_state = self._start_button_state(
            current=button_state,
            running=running,
            executor_alive=executor_alive,
            stats_age=stats_age,
            stats_fresh=stats_fresh,
            stats=stats,
            ticks=ticks,
            genomes=genomes,
        )

        winrate_ok = isinstance(winrate, (int, float))
        sharpe_ok = isinstance(sharpe_value, (int, float)) and bool(sharpe_value)
        roi_color = self._roi_color_key(roi_pct)
        roi_band = self._roi_band_text(roi_pct)
        roi_bar_value = int(round((self._clip(roi_pct, -2.0, 2.0) + 2.0) / 4.0 * 100.0))
        sound_profile = data.get("sound_profile", {}) if isinstance(data.get("sound_profile"), dict) else {}
        sound_phrases = sound_profile.get("phrases", {}) if isinstance(sound_profile.get("phrases"), dict) else {}
        sound_sample = ""
        for phrase_key in (action, "HOLD", "BUY", "SELL"):
            bucket = sound_phrases.get(phrase_key, [])
            if bucket:
                sound_sample = str(bucket[0])
                break
        if not sound_sample:
            sound_sample = str(sound_profile.get("sample", "—") or "—")

        return {
            "runtime": {
                "supported": bool(supported),
                "running": running,
                "stats_age": stats_age,
                "executor_alive": executor_alive,
                "stats_fresh": stats_fresh,
            },
            "header": {
                "status_text": self._status_text(texts, bool(supported), running, stats, stats_age, process_count, genomes, ticks),
                "sentiment_text": f"{sentiment_icon} {sentiment_text}",
                "sentiment_color": sentiment_color,
                "llm_strip_running": running,
                "llm_strip_action": action,
            },
            "consensus": {
                "label": f"CONSENSUS {action}",
                "color": cons_color,
                "pct_text": f"{agree_pct}%",
                "bar_value": agree_pct,
                "timing_text": f"Timing {llm8_timing:.2f}x",
                "rr_text": f"R/R {llm9_rr:.1f}:1",
            },
            "market": {
                "bid_text": self._format_price(bid_value),
                "bid_value": self._as_float(bid_value, 0.0),
                "ask_text": self._format_price(ask_value),
                "spread_text": self._format_float(spread_value, 1),
                "session_text": str(session_value),
                "regime_text": ("LIVE" + (f" {trend_value[:4]}" if trend_value else "")) if running else "OFF",
            },
            "indicators": {
                "rsi_text": self._format_float(rsi_value, 1),
                "adx_text": self._format_float(adx_value, 1),
                "macd_text": self._format_float(stats.get("ind_macd"), 4),
                "atr_text": self._format_float(stats.get("ind_atr"), 4),
                "stoch_text": self._format_float(stats.get("ind_stoch"), 1),
                "bbw_text": self._format_float(stats.get("ind_bbw"), 2),
                "rsi_value": int(rsi_value),
                "rsi_color": rsi_color,
            },
            "ml": {
                "dnn_text": f"{dnn_value:+.2f}" if dnn_value else "—",
                "lstm_text": f"{lstm_value:+.2f}" if lstm_value else "—",
                "rl_text": rl_value,
                "bayesian_text": f"{bay_pct}%",
                "pred_text": f"Pred {action}",
                "bull_text": f"Bull {bull_pct}%",
                "bear_text": f"Bear {100 - bull_pct}%",
                "bull_bar_value": bull_pct,
            },
            "patterns": {
                "pattern_text": pattern_text[:42] if pattern_text else ("⚡ Live telemetry" if running else "Scanning..."),
                "bull_text": f"▲Bull {pattern_bull}",
                "bear_text": f"▼Bear {pattern_bear}",
                "quality_text": f"Quality {pattern_quality}%",
            },
            "llm_votes": llm_votes,
            "attack": {
                "icon_text": attack_icon,
                "icon_color": attack_color,
                "pct_text": f"{attack_pct:.1f}%",
                "pct_value": int(attack_pct),
                "pct_color": attack_color,
                "dir_text": f"Dir {attack_dir}",
                "dir_color": attack_dir_color,
                "cool_text": attack_cool_text,
                "cool_color": attack_cool_color,
                "tooltip": f"News: {attack_tooltip_icon}{news_bias} {news_conf * 100:.0f}%",
                "gauge_value": attack_pct,
                "gauge_direction": attack_dir,
            },
            "orderflow": {
                "buy_text": str(self._as_int(stats.get("orders_sent"), 0)),
                "sell_text": str(self._as_int(stats.get("orders_acked"), 0)),
                "delta_text": str(self._as_int(stats.get("decisions_made"), 0)),
                "imbalance_text": str(self._as_int(stats.get("connection_failures"), 0)),
                "cvd_text": str(self._as_int(stats.get("trades_closed_received"), 0)),
                "open_pos_text": f"Pos {open_positions}",
                "open_pos_color": "buy" if open_positions > 0 else "dim",
            },
            "network": {
                "component_colors": tcp_colors,
                "trinity_text": f"Trinity {trinity_pct}%",
                "kraken_text": f"Kraken {kraken_acks}/{kraken_pings}",
                "sound_text": f"Sound {'ON' if tcp.get('sound') else 'OFF'}",
                "ticks_text": f"Ticks {ticks}",
                "errors_text": f"Errors {errors}",
                "llm_colors": llm_tcp_colors,
            },
            "memoria": {
                "phase_text": f"Phase {memoria.get('consciousness_phase', '—')}",
                "edge_text": f"Edge {edge_status}",
                "edge_color": edge_color,
            },
            "performance": {
                "winrate_text": f"{winrate:.1f}%" if winrate_ok else "—",
                "winrate_color": "buy" if winrate_ok and float(winrate) >= 50 else "sell",
                "pf_text": f"Net {pnl_sign}${pnl_today:.2f}",
                "sharpe_text": f"ROI {roi_pct:+.2f}%",
                "trades_text": str(trades) if trades else "0",
                "tp_hits_text": f"TP {tp_hits}",
                "tp_hits_color": "buy" if tp_hits > 0 else "dim",
                "sl_hits_text": f"SL {sl_hits}",
                "sl_hits_color": "sell" if sl_hits > 0 else "dim",
                "today_text": f"Today: {pnl_sign}${pnl_today:.2f}",
                "today_color": "success" if pnl_today >= 0 else "error",
                "roi_text": f"{roi_pct:+.2f}%",
                "roi_value": roi_pct,
                "roi_color": roi_color,
                "roi_band": roi_band,
                "roi_bar_value": roi_bar_value,
                "profit_text": f"Profit ${gross_profit:.2f}",
                "profit_color": "info",
                "loss_text": f"Loss ${gross_loss:.2f}",
                "loss_color": "sell",
                "trades_total_text": f"Trades {trades}",
                "win_count_text": f"W {wins}",
                "loss_count_text": f"L {losses}",
                "edge_sharpe_text": f"Sharpe {float(sharpe_value):.2f}" if sharpe_ok else "Sharpe —",
            },
            "sound": {
                "voice_text": str(sound_profile.get("voice", "—") or "—"),
                "persona_text": str(sound_profile.get("persona", "—") or "—"),
                "sample_text": sound_sample[:140],
            },
            "buttons": {
                "start_enabled": bool(supported and (not running or start_state == "waiting_ea")),
                "stop_enabled": bool(supported and (running or stats_age is not None)),
                "start_state": start_state,
                "reset_stop": running,
                "algo_text": texts["algo_on"] if algo_enabled else texts["algo_off"],
                "algo_tooltip": texts["algo_toggle_hint_on"] if algo_enabled else texts["algo_toggle_hint_off"],
            },
        }
