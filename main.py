import asyncio
from asyncio import AbstractEventLoop
from csv import DictWriter
from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Coroutine, Iterable, List, Tuple
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from aiohttp import ClientSession

from constants import (
    REFRESH_TIME, SERIES_KEYS_ONLY_URL, SERIES_KEYS_XML_XPATH,
    STATUS_CODE_TO_EXCEPTION, XML_NAMESPACES,
)
from logger import logger
from utils import (
    extract_date_and_value, extract_from_to_currency, get_currency_data_elements,
    get_exchange_currency_url, raise_if_error_by_status_code,
)


async def get_exchange_currency_data(url: str, client: ClientSession) -> List[Tuple[str, str]]:
    logger.debug(f'Getting exchanges from url: {url}')

    async with client.get(url) as exchange_currency_response:
        exchange_currency_xml = await exchange_currency_response.text()

    raise_if_error_by_status_code(exchange_currency_response.status)

    exchange_currency_xml_root = ET.fromstring(exchange_currency_xml)
    currency_data_elements = get_currency_data_elements(exchange_currency_xml_root)

    logger.debug(f'Successfully received exchanges from: {url}')

    return list(map(extract_date_and_value, currency_data_elements))


def get_exchange_currency_coroutines(client: ClientSession, urls: Iterable[str]) -> Iterable[Coroutine]:
    return (
        get_exchange_currency_data(exchange_currency_url, client)
        for exchange_currency_url
        in urls
    )


@dataclass
class CurrencyExchangeData:
    from_currency: str
    to_currency: str
    date: date
    rate: str


async def data_collector(loop: AbstractEventLoop):
    series_keys_only_request = Request(SERIES_KEYS_ONLY_URL)
    series_keys_only_response = urlopen(series_keys_only_request)
    series_keys_only_xml = series_keys_only_response.read().decode()
    series_keys_only_xml_root = ET.fromstring(series_keys_only_xml)

    series_data: Iterable[ET.Element] = series_keys_only_xml_root.findall(SERIES_KEYS_XML_XPATH, XML_NAMESPACES)
    from_to_currencies: Tuple[Tuple[str, str]] = tuple(map(extract_from_to_currency, series_data))
    exchange_currency_urls: Tuple[str, ...] = tuple(map(get_exchange_currency_url, from_to_currencies))

    async with ClientSession(loop=loop) as client:
        results = await asyncio.gather(*get_exchange_currency_coroutines(client, exchange_currency_urls))

    currency_exchanges_data = []

    for from_to, currency_data in zip(from_to_currencies, results):
        from_currency, to_currency = from_to
        last_know_rate = None
        for rate_data in currency_data:
            rate_date, rate = rate_data
            rate = rate if rate != 'NaN' else last_know_rate
            last_know_rate = rate
            currency_exchanges_data.append(
                CurrencyExchangeData(
                    from_currency=from_currency,
                    to_currency=to_currency,
                    date=datetime.strptime(rate_date, '%Y-%m-%d').date(),
                    rate=rate
                )
            )

    currency_exchanges_data = sorted(currency_exchanges_data, key=lambda x: x.date)

    with open('results.csv', 'w') as file:
        writer = DictWriter(file, fieldnames=CurrencyExchangeData.__annotations__.keys())
        writer.writeheader()
        for ce in currency_exchanges_data:
            writer.writerow(asdict(ce))


async def main(loop: AbstractEventLoop):
    try:
        logger.info('Starting data collecting...')
        await data_collector(loop)
        logger.success('Data collected successfully! Refresh in %i seconds' % REFRESH_TIME)
        await asyncio.sleep(REFRESH_TIME)
    except STATUS_CODE_TO_EXCEPTION.get(503) as internal_exception:
        logger.warning(internal_exception.get_message())
        await asyncio.sleep(internal_exception.restart_time)
        await main(loop)


if __name__ == '__main__':
    loop_ = asyncio.get_event_loop()
    try:
        loop_.run_until_complete(main(loop_))
    except KeyboardInterrupt:
        logger.info('Stopping...')
    except Exception as exception:
        logger.critical(exception)
        raise exception
