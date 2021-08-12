from typing import Dict, Type

from exceptions import BaseSDMXException, ServiceUnavailable

SERIES_KEYS_ONLY_URL: str = 'https://sdw-wsrest.ecb.europa.eu/service/data/EXR/D....?detail=serieskeysonly'
EXCHANGE_CURRENCY_URL_PATTERN: str = 'https://sdw-wsrest.ecb.europa.eu/service/data/EXR/D.%s.%s..'
SERIES_KEYS_XML_XPATH = 'message:DataSet/generic:Series/generic:SeriesKey'
OBS_XML_XPATH = 'message:DataSet/generic:Series/generic:Obs'
XML_NAMESPACES = {
    'message': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message',
    'generic': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic',
}
STATUS_CODE_TO_EXCEPTION: Dict[int, Type[BaseSDMXException]] = {
    503: ServiceUnavailable,
}
REFRESH_TIME: int = 60 * 10