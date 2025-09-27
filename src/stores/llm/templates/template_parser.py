import os


class TemplateParser:
    
    def __init__(self, language: str, default_language: str = "en"):
        self.language = None
        self.default_language = default_language
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.set_language(language=language)
    
    def set_language(self, language: str):

        language_path = os.path.join(self.current_dir, "locales", language)

        if not language or not os.path.exists(language_path):
            self.language = self.default_language
        elif os.path.exists(language_path):
            self.language = language

    def load_template(self, group: str, key: str, vars: dict={}):
        language_path = os.path.join(self.current_dir, "locales", self.language, f"{group}.py")
        target_language = self.language
        if not os.path.exists(language_path):
            language_path = os.path.join(self.current_dir, "locales", self.default_language, f"{group}.py")
            target_language = self.default_language

        if not os.path.exists(language_path):
            return None
        
        #import the module from the file path

        module = __import__(f"stores.llm.templates.locales.{target_language}.{group}", fromlist=[group])
        if not module:
            return None
        
        key_attribute = getattr(module, key)
        return key_attribute.substitute(vars) if key_attribute else None