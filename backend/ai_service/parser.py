try:
    from .outline_schema import OutlinePromptSchema, OutlineBuildSchema
except ImportError:
    from outline_schema import OutlinePromptSchema, OutlineBuildSchema
from langchain_core.output_parsers import PydanticOutputParser

def OutlinePromptParser():
    return PydanticOutputParser(pydantic_object=OutlinePromptSchema)


def OutlineBuildParser():
    return PydanticOutputParser(pydantic_object=OutlineBuildSchema)


def OutlineParser():
    return OutlinePromptParser()
