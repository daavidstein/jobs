from typing import Iterable, Tuple

def get_location_indicators(tree) -> Tuple[str,str]:
    #greenhouse
    div = tree.xpath(f'/html/body//div[@class="location"]/text()')[0].strip().lower()
    description = tree.xpath(f'/html//meta[@property="og:description"]')[0].values()[1].lower()

    return div, description

def is_remote(location_indicators: Iterable[str]) -> bool:
    return any(["remote" in s for s in location_indicators])
