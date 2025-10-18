import json
from typing import Dict, Any, Set, List, Optional
from bs4 import BeautifulSoup
from guardrails import OnFailAction
from loguru import logger

_ALLOWED_TAGS = {
    "html","head","body","div","main","header","footer","nav","section","article",
    "ul","ol","li","span","p","img","a","button","h1","h2","h3","h4","h5","h6",
    "input","label","form","textarea","select","option"
}
_ALLOWED_ATTRS = {"class","id","src","alt","href","type","value","placeholder","aria-label","role","for","name"}
_TW_ALLOWED_PREFIXES = (
    "container","grid","col-","row-","flex","items-","justify-","content-","gap-",
    "p-","px-","py-","pt-","pb-","pl-","pr-","m-","mx-","my-","mt-","mb-","ml-","mr-",
    "w-","h-","min-w-","min-h-","max-w-","max-h-",
    "bg-","text-","font-","leading-","tracking-","uppercase","lowercase","capitalize",
    "rounded","rounded-","border","border-","shadow","shadow-","hover:","focus:","md:","lg:","xl:","2xl:"
)

def _class_ok(token: str) -> bool:
    return token == "" or token.startswith(_TW_ALLOWED_PREFIXES)

class DomWhitelistTagsAndTailwindClasses:
    """Restringe tags, atributos y clases Tailwind a un conjunto conocido/seguro."""
    rail_alias = "dom_whitelist"
    name = "dom_whitelist"

    def __init__(self, on_fail: OnFailAction = OnFailAction.EXCEPTION):
        self.on_fail = on_fail

    def _fail(self, msg: str):
        if self.on_fail == OnFailAction.EXCEPTION:
            raise ValueError(msg)
        logger.warning(msg)

    def validate(self, value: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        try:
            data: Dict[str, Any] = json.loads(value)
            html_code = data.get("html_code", "")
        except Exception:
            self._fail("[DomWhitelist] Resultado no parseable o sin 'html_code'.")
            return value

        soup = BeautifulSoup(html_code, "html.parser")
        for tag in soup.find_all(True):
            if tag.name not in _ALLOWED_TAGS:
                self._fail(f"[DomWhitelist] Tag <{tag.name}> no permitted.")

            for attr in list(tag.attrs.keys()):
                if attr not in _ALLOWED_ATTRS:
                    self._fail(f"[DomWhitelist] Attribute '{attr}' no permitted in <{tag.name}>.")

            if tag.has_attr("class"):
                cls_tokens: List[str] = tag["class"] if isinstance(tag["class"], list) else str(tag["class"]).split()
                for tok in cls_tokens:
                    if not _class_ok(str(tok)):
                        self._fail(f"[DomWhitelist] Tailwind class not permitted: '{tok}'.")

        return value
