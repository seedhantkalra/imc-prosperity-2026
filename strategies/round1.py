class Trader:
    def __init__(self):
        self.position_limits = {"ASH_COATED_OSMIUM": 80, "INTARIAN_PEPPER_ROOT": 80}

    def run(self, state: TradingState) -> Tuple[Dict[str, List[Order]], int, str]:
        result = {}
        conversions = 0

        cache = {}
        if state.traderData:
            try:
                cache = json.loads(state.traderData)
            except Exception:
                pass

        for product in state.order_depths:
            if product not in self.position_limits: continue

            order_depth = state.order_depths[product]
            orders = []
            position = state.position.get(product, 0)
            limit = self.position_limits[product]
            max_buy_vol = limit - position
            max_sell_vol = limit + position

            best_bid = max(order_depth.buy_orders.keys()) if order_depth.buy_orders else None
            best_ask = min(order_depth.sell_orders.keys()) if order_depth.sell_orders else None

            # ============================================================
            # ASH COATED OSMIUM - The Locked 3.1k Lawnmower
            # ============================================================
            if product == "ASH_COATED_OSMIUM":
                safe_bid = best_bid if best_bid is not None else 9998
                safe_ask = best_ask if best_ask is not None else 10002

                # Immediate Taker Sweep
                if order_depth.sell_orders:
                    for ask_price, ask_vol in sorted(order_depth.sell_orders.items()):
                        if ask_price < 10000 and max_buy_vol > 0:
                            vol = min(abs(ask_vol), max_buy_vol)
                            orders.append(Order(product, int(ask_price), vol))
                            max_buy_vol -= vol; position += vol

                if order_depth.buy_orders:
                    for bid_price, bid_vol in sorted(order_depth.buy_orders.items(), reverse=True):
                        if bid_price > 10000 and max_sell_vol > 0:
                            vol = min(abs(bid_vol), max_sell_vol)
                            orders.append(Order(product, int(bid_price), -vol))
                            max_sell_vol -= vol; position -= vol

                # Void-Proof Static Pennying
                my_bid = int(safe_bid + 1)
                my_ask = int(safe_ask - 1)

                if my_bid >= 10000: my_bid = 9999
                if my_ask <= 10000: my_ask = 10001

                if position >= limit:
                    orders.append(Order(product, 10000, -limit))
                elif position <= -limit:
                    orders.append(Order(product, 10000, limit))
                else:
                    if max_buy_vol > 0: orders.append(Order(product, my_bid, max_buy_vol))
                    if max_sell_vol > 0: orders.append(Order(product, my_ask, -max_sell_vol))

                result[product] = orders
                continue

            # ============================================================
            # INTARIAN PEPPER ROOT - Pure Macro Regime Tracker
            # ============================================================
            elif product == "INTARIAN_PEPPER_ROOT":
                if best_bid is None or best_ask is None:
                    continue

                naive_mid = (best_bid + best_ask) / 2.0

                # 1. DYNAMIC ANCHORING (Zero 10k Hardcodes)
                if "PEPPER_START_PRICE" not in cache:
                    # Subtract historical drift to guarantee the true Start Price
                    # even if the bot is booted up at Tick 50,000.
                    historical_drift = state.timestamp / 1000.0
                    cache["PEPPER_START_PRICE"] = best_ask - historical_drift

                start_price = cache["PEPPER_START_PRICE"]
                theoretical_fv = start_price + (state.timestamp / 1000.0)

                # 2. FAST 10-TICK REGIME TRACKER (1,000 timestamps)
                if "PR_HISTORY" not in cache:
                    cache["PR_HISTORY"] = []

                cache["PR_HISTORY"].append(naive_mid)
                # Keep exactly 11 items to measure a 10-tick delta
                if len(cache["PR_HISTORY"]) > 11:
                    cache["PR_HISTORY"].pop(0)

                # Assume standard 0.1 drift until we have 10 ticks to prove otherwise
                empirical_drift = 0.1
                if len(cache["PR_HISTORY"]) >= 10:
                    past_mid = cache["PR_HISTORY"][0]
                    ticks_elapsed = len(cache["PR_HISTORY"]) - 1
                    empirical_drift = (naive_mid - past_mid) / ticks_elapsed

                # 3. EXECUTION
                if max_buy_vol > 0:
                    # REGIME A: Escalator is running (Drift is intact)
                    if empirical_drift >= 0.05:
                        if best_ask <= theoretical_fv + 3.0:
                            l1_ask_vol = abs(order_depth.sell_orders[best_ask])
                            take_vol = min(l1_ask_vol, max_buy_vol)
                            orders.append(Order(product, best_ask, take_vol))

                    # REGIME B: Escalator is broken (Flatline or Drop)
                    else:
                        # Fallback to pure market making
                        my_bid = int(best_bid + 1)
                        if my_bid >= best_ask: my_bid = int(best_ask - 1)
                        orders.append(Order(product, my_bid, max_buy_vol))

                result[product] = orders
                continue

        trader_data_state = json.dumps(cache)
        return result, conversions, trader_data_state
