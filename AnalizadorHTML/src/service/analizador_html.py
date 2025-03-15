from typing import List, Tuple, Dict
import re
from multiprocessing import Process, Queue

# Definición de tokens para HTML
TOKENS = {
    "TAG_OPEN": r"<[a-zA-Z][a-zA-Z0-9]*",  # Apertura de etiqueta: <div
    "TAG_CLOSE": r"</[a-zA-Z][a-zA-Z0-9]*>",  # Cierre de etiqueta: </div>
    "SELF_CLOSING_TAG": r"<[a-zA-Z][a-zA-Z0-9]*\s*/?>",  # Etiquetas autocerradas: <img />, <input />
    "ATTRIBUTE": r'[a-zA-Z_][a-zA-Z0-9_]*="[^"]*"',  # Atributos: href="..."
    "TEXT": r"[^<]+",  # Texto entre etiquetas
    "COMMENT": r"<!--.*?-->",  # Comentarios HTML
    "WHITESPACE": r"\s+",  # Espacios en blanco
    "UNKNOWN": r".",  # Caracteres no reconocidos
}

# Lista de etiquetas autocerradas (no requieren cierre)
SELF_CLOSING_TAGS = {"img", "input", "br", "meta", "link", "hr"}

# Atributos permitidos por etiqueta
ALLOWED_ATTRIBUTES = {
    "button": ["onclick", "class", "id", "style"],
    "div": ["class", "id", "style"],
    "img": ["src", "alt", "class", "id", "style"],
    "input": ["type", "name", "value", "class", "id", "style"],
    "br": [],  # <br /> no tiene atributos
    "meta": ["charset", "name", "content"],
}

# Autómata finito para reconocer tokens
class HTMLLexer:
    def __init__(self, input_text: str):
        self.input_text = input_text
        self.position = 0
        self.tokens = []
        self.errors = []

    def tokenize(self) -> List[Tuple[str, str]]:
        while self.position < len(self.input_text):
            match = None
            for token_type, pattern in TOKENS.items():
                regex = re.compile(pattern)
                match = regex.match(self.input_text, self.position)
                if match:
                    value = match.group(0)
                    if token_type == "COMMENT" or token_type == "WHITESPACE":
                        # Ignorar comentarios y espacios en blanco
                        pass
                    else:
                        self.tokens.append((token_type, value))
                    self.position = match.end()
                    break
            if not match:
                self.errors.append(f"Error léxico: Carácter no reconocido en la posición {self.position}: '{self.input_text[self.position]}'")
                self.position += 1  # Avanzar para evitar bucles infinitos
        return self.tokens

    def get_errors(self) -> List[str]:
        return self.errors

# Función para leer el contenido de un archivo
def read_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

# Función para validar la estructura del HTML
def validate_html_structure(tokens: List[Tuple[str, str]]) -> List[str]:
    errors = []
    tag_stack = []  # Pila para verificar el balance de etiquetas

    for token_type, value in tokens:
        if token_type == "TAG_OPEN":
            tag_name = re.match(r"<([a-zA-Z][a-zA-Z0-9]*)", value).group(1)
            if tag_name.lower() not in SELF_CLOSING_TAGS:
                tag_stack.append(tag_name)  # Apilar etiqueta de apertura
        elif token_type == "TAG_CLOSE":
            tag_name = re.match(r"</([a-zA-Z][a-zA-Z0-9]*)>", value).group(1)
            if not tag_stack:
                errors.append(f"Error de estructura: Etiqueta de cierre </{tag_name}> sin etiqueta de apertura correspondiente.")
            elif tag_stack[-1] != tag_name:
                errors.append(f"Error de estructura: Etiqueta de cierre </{tag_name}> no coincide con la etiqueta de apertura <{tag_stack[-1]}>.")
            else:
                tag_stack.pop()  # Desapilar etiqueta de apertura correspondiente
        elif token_type == "SELF_CLOSING_TAG":
            tag_name = re.match(r"<([a-zA-Z][a-zA-Z0-9]*)", value).group(1)
            if tag_name.lower() not in SELF_CLOSING_TAGS:
                errors.append(f"Error de estructura: La etiqueta <{tag_name}> no es autocerrada, pero se usó como tal.")

    # Verificar si quedaron etiquetas sin cerrar
    if tag_stack:
        for tag in tag_stack:
            errors.append(f"Error de estructura: Etiqueta <{tag}> no fue cerrada.")

    return errors

# Función para validar los atributos de una etiqueta
def validate_attributes(tag_name: str, attributes: List[str]) -> List[str]:
    errors = []
    allowed_attributes = ALLOWED_ATTRIBUTES.get(tag_name, [])
    for attr in attributes:
        attr_name = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)="', attr).group(1)
        if attr_name not in allowed_attributes:
            errors.append(f"Error de atributo: El atributo '{attr_name}' no está permitido en la etiqueta <{tag_name}>.")
    return errors

# Función para procesar una fuente de entrada y enviar resultados a una Queue
def process_source(file_path: str, result_queue: Queue):
    content = read_file(file_path)
    lexer = HTMLLexer(content)
    tokens = lexer.tokenize()
    errors = lexer.get_errors()

    # Validar estructura del HTML
    structure_errors = validate_html_structure(tokens)
    errors.extend(structure_errors)

    # Validar atributos de las etiquetas
    for i, (token_type, value) in enumerate(tokens):
        if token_type == "TAG_OPEN" or token_type == "SELF_CLOSING_TAG":
            tag_name = re.match(r"<([a-zA-Z][a-zA-Z0-9]*)", value).group(1)
            # Extraer atributos de la etiqueta
            attributes = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*="[^"]*")', value)
            attribute_errors = validate_attributes(tag_name, attributes)
            errors.extend(attribute_errors)

    result_queue.put({"file_path": file_path, "tokens": tokens, "errors": errors})

# Función principal para procesar múltiples fuentes de entrada concurrentemente
def process_sources_concurrently(file_paths: List[str]) -> List[Dict]:
    result_queue = Queue()
    processes = []

    # Crear un proceso por cada archivo
    for file_path in file_paths:
        process = Process(target=process_source, args=(file_path, result_queue))
        processes.append(process)
        process.start()

    # Esperar a que todos los procesos terminen
    for process in processes:
        process.join()

    # Recoger los resultados de la Queue
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())

    return results