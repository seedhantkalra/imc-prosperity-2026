class Trader:
    def __init__(self):
        self.position_limits = {"ASH_COATED_OSMIUM": 80, "INTARIAN_PEPPER_ROOT": 80}

    def run(self, state: TradingState) -> Tuple[Dict[str, List[Order]], int, str]:
        result = {}
        conversions = 0
        trader_data = state.traderData if state.traderData else ""

        for product in state.order_depths:
            if product not in self.position_limits: continue

            order_depth = state.order_depths[product]
            orders = []
            position = state.position.get(product, 0)
            limit = self.position_limits[product]
            max_buy_vol = limit - position
            max_sell_vol = limit + position

            # We DO NOT skip the tick if the book is empty anymore!
            best_bid = max(order_depth.buy_orders.keys()) if order_depth.buy_orders else None
            best_ask = min(order_depth.sell_orders.keys()) if order_depth.sell_orders else None

            # ============================================================
            # ASH COATED OSMIUM - The Void-Proof Lawnmower
            # ============================================================
            if product == "ASH_COATED_OSMIUM":
                # 1. Handle the Air Pockets
                safe_bid = best_bid if best_bid is not None else 9998
                safe_ask = best_ask if best_ask is not None else 10002

                # 2. Immediate Taker Sweep (Favorable Trades)
                if order_depth.sell_orders:
                    for ask_price, ask_vol in sorted(order_depth.sell_orders.items()):
                        if ask_price < 10000 and max_buy_vol > 0:
                            vol = min(abs(ask_vol), max_buy_vol)
                            orders.append(Order(product, ask_price, vol))
                            max_buy_vol -= vol; position += vol
                            
                if order_depth.buy_orders:
                    for bid_price, bid_vol in sorted(order_depth.buy_orders.items(), reverse=True):
                        if bid_price > 10000 and max_sell_vol > 0:
                            vol = min(abs(bid_vol), max_sell_vol)
                            orders.append(Order(product, bid_price, -vol))
                            max_sell_vol -= vol; position -= vol

                # 3. Sequential Maker Pennying (Void-Proof)
                my_bid = safe_bid + 1
                my_ask = safe_ask - 1
                
                # Maintain edge: Never bid >= 10k or ask <= 10k unless flattening
                if my_bid >= 10000: my_bid = 9999
                if my_ask <= 10000: my_ask = 10001

                # 4. Inventory Flattening (Risk Capacity Reset)
                if position >= limit: # Full Long
                    orders.append(Order(product, 10000, -limit)) # Flatten at fair value
                elif position <= -limit: # Full Short
                    orders.append(Order(product, 10000, limit))
                else:
                    if max_buy_vol > 0: orders.append(Order(product, my_bid, max_buy_vol))
                    if max_sell_vol > 0: orders.append(Order(product, my_ask, -max_sell_vol))

            # ============================================================
            # INTARIAN PEPPER ROOT - L1 Drip-Feed (The Train)
            # ============================================================
            elif product == "INTARIAN_PEPPER_ROOT":
                # Only sweep if there is actually someone selling
                if best_ask is not None and max_buy_vol > 0:
                    l1_ask_vol = abs(order_depth.sell_orders[best_ask])
                    take_vol = min(l1_ask_vol, max_buy_vol)
                    orders.append(Order(product, best_ask, take_vol))
            
            result[product] = orders

        return result, conversions, trader_data
