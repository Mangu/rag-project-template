from typing import List
from promptflow import tool
from dataclasses import dataclass
#from promptflow_vectordb.core.contracts import SearchResultEntity

@dataclass
class SearchResultEntity:
    content: str = None
    summary: str = None    
    score: float = None    
    source: str = None
    page: str = None

    @classmethod
    def from_dict(cls, data: dict) -> 'SearchResultEntity':
        instance = cls()
        instance.content = data.get('content')
        instance.summary = data.get('semantic_summary')
        instance.score = data.get('score')
        instance.source = data.get('source')
        instance.page = data.get('page')
        return instance

@tool
def generate_prompt_context(search_result: List[dict]) -> str:
    def format_doc(doc: dict):
        return f"Content: {doc['Content']}\nSource: {doc['Source']}"
        
    retrieved_docs = []
    for item in search_result:
        entity = SearchResultEntity.from_dict(item) 

        #can use some logic to ensure content, source and page are present
        retrieved_docs.append({
            "Content": entity.content,
            "Source": entity.source,
            "Page": entity.page
        }
    )
    doc_string = "\n\n".join([format_doc(doc) for doc in retrieved_docs])

    print (doc_string)
    
    return doc_string
