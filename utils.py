from typing import Collection, Optional, Tuple, Type
from xml.etree import ElementTree

from constants import EXCHANGE_CURRENCY_URL_PATTERN, OBS_XML_XPATH, STATUS_CODE_TO_EXCEPTION, XML_NAMESPACES
from exceptions import BaseSDMXException


def get_exchange_currency_url(from_to_currency: Tuple[str, str]) -> str:
    from_currency, to_currency = from_to_currency

    return EXCHANGE_CURRENCY_URL_PATTERN % (from_currency, to_currency)


def extract_from_to_currency(element: ElementTree.Element) -> Tuple[str, str]:
    return (
        element.find("*[@id='CURRENCY']").attrib.get('value'),
        element.find("*[@id='CURRENCY_DENOM']").attrib.get('value')
    )


def extract_date_and_value(element: ElementTree.Element) -> Tuple[str, str]:
    return (
        element.find('generic:ObsDimension', XML_NAMESPACES).attrib.get('value'),
        element.find('generic:ObsValue', XML_NAMESPACES).attrib.get('value'),
    )


def get_currency_data_elements(element: ElementTree.Element) -> Collection[ElementTree.Element]:
    return element.findall(OBS_XML_XPATH, XML_NAMESPACES)


def get_exception_by_status_code(code: int) -> Optional[Type[BaseSDMXException]]:
    return STATUS_CODE_TO_EXCEPTION.get(code, None)


def raise_if_error_by_status_code(code: int) -> None:
    exception_class: Optional[Type[BaseSDMXException]] = get_exception_by_status_code(code)

    if exception_class is not None:
        raise exception_class()
