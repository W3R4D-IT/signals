import uuid
from datetime import datetime
from typing import List
from fastapi import HTTPException

from api.utils import (
    clean_price_string,
    convert_to_minutes,
)


class SignalReshaper:
    @staticmethod
    def reshape_standard_signal(signal: dict, label_id: int) -> dict:
        hit = SignalReshaper.format_hit_field(signal)

        reshaped_signal = {
            "tv_signal_id": f"{signal['tv_signal_id']}_{label_id}",
            "timestamp_utc": signal["timestamp_utc"],
            "meta_data": {
                "description": signal["description"],
                "type": signal["type"],
                "bar_index_timestamp_utc": signal["bar_index_timestamp_utc"],
                "bar_index": signal["bar_index"],
            },
            "order_type": SignalReshaper.order_type_checker(signal.get("order_type")),
            "side": SignalReshaper.side_checker(signal.get("side")),
            "symbol": SignalReshaper.symbol_checker(signal.get("symbol")),
            "timeframe": SignalReshaper.timeframe_checker(signal.get("timeframe")),
            "event": SignalReshaper.event_checker(signal.get("event")),
            "hit": hit,
            "strategy": label_id,
            "entry_price": (
                SignalReshaper.check_entry_price(signal.get("entry"))
                if hit == "ENTRY"
                else "0.0"
            ),
        }

        stop_loss_data = SignalReshaper.format_stop_loss_price(
            stop_loss=signal.get("sl")
        )
        reshaped_signal.update(stop_loss_data)

        if hit == "ENTRY":
            # pass tps value from tp1 to tp8
            take_profits_data = SignalReshaper.format_take_profit_prices(
                take_profits=[signal.get(f"tp{i}") for i in range(1, 9)]
            )
            reshaped_signal.update(take_profits_data)
        else:
            reshaped_signal.update(
                {
                    "take_profit_type": "NaN",
                    "take_profit_values": ["NaN"],
                }
            )

        return reshaped_signal

    @staticmethod
    def reshape_custom_signal(signal: dict, webhook_secret_key: str) -> dict:
        reshaped_signal = {
            "tv_signal_id": SignalReshaper.generate_tv_signal_id(
                tv_signal_id=signal.get("tv_signal_id")
            ),
            "timestamp_utc": SignalReshaper.generate_timestamp_utc(
                timestamp_utc=signal.get("timestamp_utc")
            ),
            "webhook_secret": webhook_secret_key,
            "event": SignalReshaper.event_checker(signal.get("event")),
            "order_type": SignalReshaper.order_type_checker(signal.get("order_type")),
            "side": SignalReshaper.side_checker(signal.get("side")),
            "entry_price": SignalReshaper.check_entry_price(signal.get("entry")),
            "channel": signal.get("channel", "default"),
        }

        stop_loss_data = SignalReshaper.format_stop_loss_price(
            stop_loss=signal.get("sl")
        )

        #
        final_tp_index = (
            signal.get("final_tp") if signal.get("final_tp") else signal.get("tp8")
        )
        tp_value = (
            signal.get("tp") if signal.get("tp") else signal.get(f"tp{final_tp_index}")
        )
        take_profit_data = SignalReshaper.format_take_profit_price(take_profit=tp_value)

        reshaped_signal.update(stop_loss_data)
        reshaped_signal.update(take_profit_data)
        return reshaped_signal

    @classmethod
    def generate_timestamp_utc(cls, timestamp_utc) -> str:
        if timestamp_utc is not None:
            return timestamp_utc
        else:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def generate_tv_signal_id(cls, tv_signal_id) -> str:
        if tv_signal_id is not None:
            return tv_signal_id
        else:
            # generate a unique id
            return str(uuid.uuid4())

    @classmethod
    def event_checker(cls, event) -> str:
        if event is None:
            return "open"

        match event.lower():
            case "open" | "formed":
                return "open"
            case "update" | "updated":
                return "update"
            case "close" | "invalidated":
                return "close"
            case "close-all" | "close_all" | "close all":
                return "close-all"
            case _:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid event value, accepted options (open, update, close, close-all, formed, updated, invalidated)",
                )

    @classmethod
    def order_type_checker(cls, order_type) -> str:
        if order_type is None:
            return 2

        match order_type.lower():
            case "market":
                return 2
            case 1:
                return 1
            case _:
                return 2

    @classmethod
    def side_checker(cls, side) -> str:
        if side is None:
            raise HTTPException(status_code=400, detail="Side is required")

        match side.lower():
            case "buy" | "long":
                return "buy"
            case "sell" | "short":
                return "sell"
            case _:
                raise HTTPException(status_code=400, detail="Invalid side")

    @classmethod
    def symbol_checker(cls, symbol) -> str:
        if symbol is None:
            raise HTTPException(status_code=400, detail="Symbol is required")
        return symbol

    @classmethod
    def timeframe_checker(cls, timeframe) -> str:
        if timeframe is None:
            raise HTTPException(status_code=400, detail="TimeFrame is required")
        return str(convert_to_minutes(timeframe=timeframe))

    @classmethod
    def check_entry_price(cls, entry) -> str:
        if entry is None or not isinstance(entry, str):
            return "NaN"
        return clean_price_string(entry)

    @classmethod
    def format_stop_loss_price(cls, stop_loss) -> dict:
        if stop_loss is None:
            return {
                "stop_loss_type": "NaN",
                "stop_loss_value": "NaN",
            }

        if not isinstance(stop_loss, str):
            raise HTTPException(status_code=400, detail="Stop loss is invalid.")

        stop_loss = stop_loss.lower()

        if "r" in stop_loss or "rr" in stop_loss:
            raise HTTPException(
                status_code=400, detail="Stop loss can't be of type risk reward ratio."
            )

        # Stop loss has two shapes: currency or percentage
        if "%" in stop_loss:
            return {
                "stop_loss_type": "percentage",
                "stop_loss_value": clean_price_string(stop_loss.replace("%", "")),
            }
        else:
            return {
                "stop_loss_type": "currency",
                "stop_loss_value": clean_price_string(stop_loss),
            }

    @classmethod
    def format_take_profit_prices(cls, take_profits: List) -> dict:
        if not all(isinstance(tp, str) for tp in take_profits):
            raise HTTPException(
                status_code=400, detail="Take profit values are invalided."
            )

        # take profit has three shapes: currency or percentage or risk_reward
        take_profit_data = {"percentage": [], "risk_reward": [], "currency": []}
        for tp in take_profits:
            tp = tp.lower()
            # Determine type and add to the corresponding list
            if "%" in tp:
                take_profit_data["percentage"].append(
                    clean_price_string(tp.replace("%", ""))
                )
            elif "r" in tp or "rr" in tp:
                take_profit_data["risk_reward"].append(
                    clean_price_string(tp.replace("rr", "").replace("r", ""))
                )
            else:
                take_profit_data["currency"].append(clean_price_string(tp))

        # Check that only one take-profit type is used
        non_empty_types = [key for key, values in take_profit_data.items() if values]
        if len(non_empty_types) != 1:
            raise HTTPException(
                status_code=400, detail="All take-profits must be of the same type."
            )

        # Return the take-profit type and values
        take_profit_type = non_empty_types[0]
        take_profit_values = take_profit_data[take_profit_type]

        return {
            "take_profit_type": take_profit_type,
            "take_profit_values": take_profit_values,
        }

    @classmethod
    def format_take_profit_price(cls, take_profit) -> str:
        if take_profit is None:
            return {
                "take_profit_type": "NaN",
                "take_profit_values": ["NaN"],
            }

        if not isinstance(take_profit, str):
            raise HTTPException(status_code=400, detail="Take profit is invalid!")

        take_profit = take_profit.lower()

        if "%" in take_profit:
            return {
                "take_profit_type": "percentage",
                "take_profit_values": [
                    clean_price_string(take_profit.replace("%", ""))
                ],
            }
        elif "r" in take_profit or "rr" in take_profit:
            return {
                "take_profit_type": "risk_reward",
                "take_profit_values": [
                    clean_price_string(take_profit.replace("rr", "").replace("r", ""))
                ],
            }
        else:
            return {
                "take_profit_type": "currency",
                "take_profit_values": [clean_price_string(take_profit)],
            }

    @classmethod
    def format_hit_field(cls, signal: dict) -> str:
        # Check if the message contains "entry_hit"
        # ? e.g., "entry_hit": "1"
        if signal.get("entry_hit") in ["1", "2", "3", "4", "5", "6", "7", "8"]:
            return "entry".upper()

        # Check if the message contains "sl_hit"
        # ? e.g., "sl_hit": "1"
        if signal.get("sl_hit") == "1":
            return "sl".upper()

        # Loop through possible tp hits from tp1 to tp8
        # ? e.g., "tp2_hit": "1"
        for i in range(1, 9):
            tp_key = f"tp{i}_hit"
            if signal.get(tp_key) == "1":
                return f"tp{i}".upper()
