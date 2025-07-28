from googletrans import Translator

translator = Translator()

def translate_to_english(text, lang="hi"):
    if lang == "en":
        return text
    return translator.translate(text, src=lang, dest='en').text

def translate_from_english(text, lang="hi"):
    if lang == "en":
        return text
    return translator.translate(text, src='en', dest=lang).text
