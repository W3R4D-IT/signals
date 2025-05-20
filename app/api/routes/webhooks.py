import json
import re
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from urllib.parse import unquote
from sqlmodel import select

from core.broker import BrokerManager
from core.enums import EventStoreTypeEnum, RoutingTypeEnum
from core.config import settings
from api.deps import SessionDep
from models import Bot, WebHookSecret, Channel
from api.utils.signal_reshaper import SignalReshaper
from api.utils.signal_encryption import SignalEncryption
from statics import (
    DEFAULT_INDICATOR_KEYS_MAPPER,
    ENTRY_PRICE_KEY,
    STOP_LOSS_KEY,
    TAKE_PROFIT_KEY,
)

router = APIRouter()

logger = logging.getLogger(__name__)


# Verify Secret Key
def verify_secret_key_is_provided(request: Request):
    api_key = request.query_params.get("secret_key")
    if api_key is None:
        raise HTTPException(status_code=403, detail="Invalid Secret Key")


#
def verify_label_id(request: Request) -> int:
    label_id = request.query_params.get("label_id")
    if label_id is None:
        raise HTTPException(
            status_code=400, detail="label_id is required as a query parameter."
        )
    try:
        return int(label_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="label_id must be a valid integer.")


@router.post("/signals", dependencies=[Depends(verify_secret_key_is_provided)])
async def create_message(session: SessionDep, request: Request):
    try:
        # Parse query parameters
        secret_key = unquote(request.url.query.split("secret_key=")[1].split("&")[0])

        if secret_key == settings.SECRET_KEY:
            data = await request.json()
            label_id = verify_label_id(request=request)
            reshaped_signal = SignalReshaper.reshape_standard_signal(
                signal=data, label_id=label_id
            )
            publish_signal(reshaped_signal)
            return {"message": "Signals saved successfully", "data": reshaped_signal}

        else:
            reshaped_signal = await custom_wh_bot_signal(
                secret_key=secret_key, session=session, request=request
            )
            publish_signal(reshaped_signal)
            return {"message": "Signals saved successfully", "data": reshaped_signal}

    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc}")
        content_type = request.headers.get("Content-Type", "").lower()
        request_info = {
            "content_type": content_type,
            "status_code": http_exc.status_code,
            "detail": http_exc.detail,
            "body": (
                await request.body()
                if "json" in content_type
                else await (await request.body()).decode("utf-8")
            ),
        }
        logger.error(f"Request Error: {request_info}")
        raise http_exc

    except ValueError as val_err:
        # Re-raise ValueErrors directly
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as ex:
        logger.error(f"Internal server error: {ex}")
        raise HTTPException(
            status_code=500, detail=f"An internal server error occurred. Due to => {ex}"
        )


def publish_signal(reshaped_signal):
    BrokerManager(event_store_key=EventStoreTypeEnum.SIGNAL_STREAM).publish_event(
        routing_key=RoutingTypeEnum.SIGNAL_STREAM, message=reshaped_signal
    )


async def custom_wh_bot_signal(
    secret_key: str, session: SessionDep, request: Request
) -> dict:
    webhook_secret_data = get_webhook_secret_data(secret_key, session)
    bot = get_bot(webhook_secret_data.bot_id, session)

    if not bot.is_active or bot.deleted_at is not None:
        raise HTTPException(status_code=403, detail="No bots are active for this hook!")

    channel_name = await extract_channel_name(request)
    if bot.is_signal_encrypted:
        return await handle_encrypted_signal(request, channel_name, webhook_secret_data)

    channel = get_channel(channel_name, bot.id, session)
    extracted_values = await extract_predefined_indicator_values(
        request, channel.indicator_keywords_mapper or DEFAULT_INDICATOR_KEYS_MAPPER
    )
    extracted_values["channel"] = channel_name

    return SignalReshaper.reshape_custom_signal(
        signal=extracted_values,
        webhook_secret_key=webhook_secret_data.webhook_secret,
    )


def get_webhook_secret_data(secret_key: str, session: SessionDep) -> WebHookSecret:
    statement = select(WebHookSecret).where(WebHookSecret.webhook_secret == secret_key)
    webhook_secret_data = session.exec(statement).first()
    if webhook_secret_data is None:
        raise HTTPException(status_code=403, detail="Invalid Secret Key")
    return webhook_secret_data


def get_bot(bot_id: int, session: SessionDep) -> Bot:
    statement = select(Bot).where(Bot.id == bot_id)
    bot = session.exec(statement).first()
    return bot


async def extract_channel_name(request: Request) -> str:
    name = None
    try:
        name = request.query_params.get("channel", None)
        if name is None:
            data = await request.json()
            name = data.get("channel")
    except json.JSONDecodeError:
        name = "default"

    return str(name).strip()


async def handle_encrypted_signal(
    request: Request, channel_name: str, webhook_secret_data: WebHookSecret
) -> dict:
    data = await request.json()
    if not data.get("data"):
        raise HTTPException(
            status_code=400, detail="data is required in the request body."
        )

    signal = SignalEncryption.decrypt(
        ciphertext=data["data"], key=settings.ENCRYPTION_KEY
    )
    signal = json.loads(signal)
    signal["channel"] = channel_name

    return SignalReshaper.reshape_custom_signal(
        signal=signal, webhook_secret_key=webhook_secret_data.webhook_secret
    )


def get_channel(channel_name: str, bot_id: int, session: SessionDep) -> Channel:
    statement = select(Channel).where(
        Channel.name == channel_name, Channel.bot_id == bot_id
    )
    channel = session.exec(statement).first()
    if channel is None:
        raise HTTPException(
            status_code=404, detail=f"Channel {channel_name} not found!"
        )
    return channel


async def extract_predefined_indicator_values(request: Request, mapper: dict) -> dict:
    extracted_values = {}
    # List of text keys for edge cases
    text_keys = ["content", "contents", "message", "text", "body"]

    # Filter out None values from the mapper
    valid_mapper = {
        key: keyword for key, keyword in mapper.items() if keyword is not None
    }

    try:
        data = await request.json()
        extracted_values["event"] = data.get("event")
        extracted_values["side"] = data.get("side")

        # Edge case where the side is sent as description
        if bool(set(text_keys) & set(data.keys())):
            raise json.JSONDecodeError("Special case with json and text.", "data", 0)

        for key, keyword in valid_mapper.items():
            extracted_values[key] = data.get(keyword, None)

    except json.JSONDecodeError:
        content = (await request.body()).decode("utf-8")
        extracted_values["event"] = request.query_params.get("event")
        side_match = re.search(r"\b(sell|buy|long|short)\b", content, re.IGNORECASE)
        extracted_values["side"] = (
            side_match.group(1).lower()
            if side_match
            else request.query_params.get("side", None)
        )

        for key, keyword in valid_mapper.items():
            pattern = rf"{re.escape(keyword)}[:=]\s*(\d+\.?\d*)"
            match = re.search(pattern, content, re.IGNORECASE)
            extracted_values[key] = float(match.group(1)) if match else None

    sl = extracted_values.pop(STOP_LOSS_KEY, None)
    extracted_values["sl"] = str(sl) if sl else None
    tp = extracted_values.pop(TAKE_PROFIT_KEY, None)
    extracted_values["tp"] = str(tp) if tp else None
    entry = extracted_values.pop(ENTRY_PRICE_KEY, None)
    extracted_values["entry"] = str(entry) if entry else None

    return extracted_values
