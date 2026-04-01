from translator.deepl import Deepl
from default.settings import DEEPL_AUTH_KEY

DEEPL = None

def _is_set() -> bool:
    return DEEPL is not None

def _set() -> None:
    if not _is_set():
        global DEEPL
        DEEPL = Deepl(DEEPL_AUTH_KEY)

def translate_text(text, targetLang='PT-PT') -> str:
    _set()
    DEEPL.targetLang = targetLang
    DEEPL.text = text
    return DEEPL.translate(text)


def check_total_translation_usage() -> dict:
    _set()
    return DEEPL.currentUsage


def translator(targetLang: str = 'EN-GB') -> callable:
    """
    Returns a Deepl translator instance with the specified target language.
    
    Args:
        targetLang: The target language for translation.
        
    Returns:
        An instance of Deepl configured for the specified target language.
    """
    if targetLang is None or targetLang == 'EN-GB':
        return empty_translator_func
    if not _is_set():
        _set()
    DEEPL.targetLang = targetLang
    return DEEPL.translate


def empty_translator_func(text: str) -> str:
    """
    Returns the input text unchanged, used as a placeholder for no translation.
    
    Args:
        text: The text to return unchanged.
        
    Returns:
        The input text as is.
    """
    return text