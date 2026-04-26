"""
01.engine.py - 终极AI交易引擎 V5
适配 GitHub Actions 免费部署，支持 ONESHOT 模式和状态持久化
"""
import os
import time
import json
import datetime
import numpy as np
import pandas as pd

from data import get_stock_data, get_market_regime
from trader import Trader
from logger import Logger
from performance import PerformanceAnalyzer
from risk_engine import RiskEngine
from paper_broker import PaperBroker

from ml_selector import MLStockSelector
from transformer_predictor import TransformerPredictor
from rl_agent import RLAgent
from multi_agent import MultiAgentSystem

from evolution_engine import EvolutionEngine
from stress_test import StressTest


class Engine:
    def __init__(self):
        self.stock_pool = ["600519", "000001", "300750"]

        self.trader = Trader()
        self.logger = Logger()
        self.performance = PerformanceAnalyzer()
        self.risk = RiskEngine()
        self.broker = PaperBroker()

        self.ml = MLStockSelector()
        self.tf = TransformerPredictor()
        self.rl = RLAgent()
        self.agent = MultiAgentSystem()

        self.evo = EvolutionEngine()
        self.stress_tester = StressTest()

        self.capital = 100000
        self.last_price = {}

        if not hasattr(self.evo, 'model_weights') or self.evo.model_weights is None:
            self.evo.model_weights = {"ml": 0.25, "tf": 0.25, "rl": 0.25, "agent": 0.25}

        # 尝试加载上次状态
        loaded = self.load_state()
        if not loaded:
            self.trader.reset(self.capital)
            self.risk.reset(self.capital)

        # 自动加载或训练模型
        self._init_models()

    def _init_models(self):
        """模型加载：优先加载已保存模型，否则训练"""
        ml_loaded = self.ml.load_model()
        tf_loaded = self.tf.load_model()
        if not ml_loaded or not tf_loaded:
            self.logger.log("📚 模型未找到，开始训练...")
            self.train_models()

    def save_state(self):
        state = {
            "cash": self.trader.cash,
            "position": self.trader.position,
            "last_price": self.last_price,
            "model_weights": self.evo.model_weights,
            "risk_peak": self.risk.peak_value,
            "loss_streak": self.risk.loss_streak
        }
        os.makedirs("logs", exist_ok=True)
        with open("logs/engine_state.json", "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def load_state(self):
        try:
            with open("logs/engine_state.json", "r", encoding="utf-8") as f:
                state = json.load(f)
            self.trader.cash = state["cash"]
            self.trader.position = {k: v for k, v in state.get("position", {}).items()}
            self.last_price = {k: v for k, v in state.get("last_price", {}).items()}
            self.evo.model_weights = state.get("model_weights", self.evo.model_weights)
            self.risk.peak_value = state.get("risk_peak", self.trader.cash)
            self.risk.current_value = state.get("risk_peak", self.trader.cash)
            self.risk.loss_streak = state.get("loss_streak", 0)
            self.logger.log("📂 状态已恢复")
            return True
        except FileNotFoundError:
            return False

    def is_trading_time(self):
        now = datetime.datetime.now()
        if now.weekday() >= 5:
            return False
        t = now.time()
        return (datetime.time(9, 30) <= t <= datetime.time(11, 30)) or \
               (datetime.time(13, 0) <= t <= datetime.time(15, 0))

    def train_models(self):
        self.logger.log("🧠 Walk-forward训练开始")
        data = {}
        for s in self.stock_pool:
            data[s] = get_stock_data(s)

        common_dates = self._get_common_dates(data)
        if common_dates.empty:
            self.logger.log("❌ 无法找到共同日期，训练跳过")
            return

        splits = self.evo.walk_forward_split(common_dates)
        for i, (train_dates, test_dates) in enumerate(splits):
            if i >= 3:
                break
            train_data_dict = {}
            for s in self.stock_pool:
                if s in data:
                    df_s = data[s]
                    train_s = df_s.loc[df_s.index.isin(train_dates)]
                    if not train_s.empty:
                        train_data_dict[s] = train_s
            if not train_data_dict:
                continue
            self.ml.train(train_data_dict)
            self.tf.train(train_data_dict)
        self.logger.log("🏆 训练完成")

    def _get_common_dates(self, data_dict):
        date_sets = []
        for df in data_dict.values():
            if isinstance(df, pd.DataFrame) and not df.empty:
                try:
                    dates = pd.to_datetime(df.index).unique()
                    date_sets.append(set(dates))
                except:
                    pass
        if not date_sets:
            return pd.DatetimeIndex([])
        common = sorted(list(set.intersection(*date_sets)))
        return pd.DatetimeIndex(common)

    def _current_total_asset(self):
        prices = {}
        for stock in list(self.trader.position.keys()) + self.stock_pool:
            try:
                df = get_stock_data(stock)
                if not df.empty:
                    prices[stock] = df.iloc[-1]['close']
            except:
                pass
        return self.trader.get_total_asset(prices)

    def _score_stock(self, prices):
        ml_s = self.ml.predict_score(prices)
        tf_s = self.tf.predict_score(prices)
        state = self.rl.get_state(prices)
        rl_a = self.rl.choose_action(state)
        ag_a, _ = self.agent.vote(prices)

        # 市场状态自适应权重
        regime = get_market_regime(prices)
        w = self.evo.model_weights.copy()
        if regime == "trend":
            w["ml"] *= 1.5
            w["agent"] *= 1.2
        elif regime == "mean_reversion":
            w["ml"] *= 0.8
            w["rl"] *= 1.5
        elif regime == "volatile":
            for k in w:
                w[k] *= 0.6

        score = (
            w["ml"] * ml_s +
            w["tf"] * tf_s +
            w["rl"] * (1 if rl_a == "BUY" else -1) +
            w["agent"] * (1 if ag_a == "BUY" else -1)
        )
        return score, ag_a

    def run_once(self):
        if not self.is_trading_time():
            self.logger.log("⏸️ 非交易时间，等待")
            return

        self.logger.log("🚀 引擎运行")
        total_asset = self._current_total_asset()
        self.risk.update_portfolio(total_asset)

        allow, reason = self.risk.allow_trade()
        if not allow:
            self.logger.log(f"🛑 风控熔断: {reason}")
            return

        # ---- 卖出 ----
        for stock in list(self.trader.position.keys()):
            try:
                prices = get_stock_data(stock)
                if prices.empty:
                    continue
                price = prices.iloc[-1]['close']
            except:
                continue
            try:
                score, ag_a = self._score_stock(prices)
            except:
                continue
            if score < -5 or ag_a == "SELL":
                amount = self.trader.position.get(stock, 0)
                if amount > 0:
                    result = self.trader.sell(stock, price, amount, self.broker)
                    if result:
                        self.logger.trade(stock, "SELL", price, amount)
                        self.performance.record_trade(stock=stock, price=price, amount=amount,
                                                      cash_before=result["cash_before"],
                                                      cash_after=result["cash_after"], action="SELL")
                        if stock in self.last_price:
                            reward = price - self.last_price[stock]
                            self.evo.evolve(reward)
                            self.risk.update_trade_result(reward)
                        self.last_price.pop(stock, None)

        # ---- 买入 ----
        best = None
        for stock in self.stock_pool:
            if stock in self.trader.position:
                continue
            try:
                prices = get_stock_data(stock)
                if prices.empty:
                    continue
                price = prices.iloc[-1]['close']
            except:
                continue
            try:
                score, _ = self._score_stock(prices)
            except:
                continue
            self.logger.log(f"{stock} | score={score:.2f}")
            if score > 10 and (best is None or score > best["score"]):
                best = {"stock": stock, "price": price, "score": score}

        if best:
            stock = best["stock"]
            price = best["price"]
            trade_cash = min(total_asset * 0.1, total_asset * 0.2)
            amount = int(trade_cash / price) if price > 0 else 0
            if amount > 0:
                result = self.trader.buy(stock, price, amount, self.broker)
                if result:
                    self.logger.trade(stock, "BUY", price, amount)
                    self.performance.record_trade(stock=stock, price=price, amount=amount,
                                                  cash_before=result.get("cash_before", 0),
                                                  cash_after=result.get("cash_after", 0), action="BUY")
                    if stock in self.last_price:
                        reward = price - self.last_price[stock]
                        self.evo.evolve(reward)
                        self.risk.update_trade_result(reward)
                    self.last_price[stock] = price

        # 收盘保存状态
        now = datetime.datetime.now()
        if now.time() >= datetime.time(15, 0):
            self.save_state()
            self.logger.log("💾 收盘状态已保存")

    def run_stress_test(self):
        self.logger.log("🧪 压力测试启动")
        for stock in self.stock_pool:
            try:
                prices = get_stock_data(stock)
                crash_result = self.stress_tester.simulate_crash(prices)
                self.logger.log(f"{stock} crash test score = {np.mean(crash_result)}")
            except Exception as e:
                self.logger.log(f"⚠️ {stock} 压力测试出错: {e}")

    def run(self):
        self.logger.log("🔄 系统开始运行")
        # 如果是 GitHub Actions 调用（环境变量 ONESHOT=1），则只执行一次
        if os.environ.get("ONESHOT") == "1":
            self.run_once()
            self.save_state()
            self.logger.log("✅ 单次执行完成，状态已保存")
        else:
            try:
                while True:
                    self.run_once()
                    time.sleep(20)
            except KeyboardInterrupt:
                self.save_state()
                self.logger.log("⏹️ 手动中断，状态已保存")
            except Exception as e:
                self.save_state()
                self.logger.log(f"💥 异常终止，状态已保存: {e}")


if __name__ == "__main__":
    Engine().run()