from outline_schema import OutlinePromptSchema
from langchain_core.output_parsers import PydanticOutputParser

def OutlineParser():
    parser = PydanticOutputParser(
        pydantic_object=OutlinePromptSchema
    )
    return parser