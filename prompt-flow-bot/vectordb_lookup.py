import json
import re
import requests
from promptflow import tool
from promptflow.connections import AzureOpenAIConnection
from promptflow.connections import CognitiveSearchConnection

def get_query_list(query):
    try:
        config = json.loads(query)
        return config
    except Exception:
        return [query]

def get_query_embedding(query, endpoint, api_key, api_version, embedding_model_deployment):
    request_url = f"{endpoint}/openai/deployments/{embedding_model_deployment}/embeddings?api-version={api_version}"
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    request_payload = {
        'input': query
    }
    embedding_response = requests.post(request_url, json = request_payload, headers = headers, timeout=None)
   
    if embedding_response.status_code == 200:
        data_values = embedding_response.json()["data"]
        embeddings_vectors = [data_value["embedding"] for data_value in data_values]
        return embeddings_vectors
    else:
        raise Exception(f"failed to get embedding: {embedding_response.json()}")

def search_query_api(endpoint, api_key, api_version, index_name, query_type, query, top_k, embedding_connection, 
                     embedding_model = None, semantic_configuration_name=None, vector_fields=None):
    
    request_url = f"{endpoint}/indexes/{index_name}/docs/search?api-version={api_version}"
    request_payload = {
        'top': top_k,
        'queryLanguage': 'en-us'
    }
    if query_type == 'simple':
        request_payload['search'] = query
        request_payload['queryType'] = query_type
    elif query_type == 'semantic':
        request_payload['search'] = query
        request_payload['queryType'] = query_type
        request_payload['semanticConfiguration'] = semantic_configuration_name
    elif query_type in ('vector', 'vector_simple_hybrid', 'vector_semantic_hybrid'):
        if vector_fields and embedding_model:
            query_vectors = get_query_embedding(
                query,
                embedding_connection["api_base"],
                embedding_connection["api_key"],
                embedding_connection["api_version"],
                embedding_model
            )
            payload_vectors = [{"value": query_vector, "fields": vector_fields, "k": top_k } for query_vector in query_vectors]
            request_payload['vectors'] = payload_vectors

        if query_type == 'vector_simple_hybrid':
            request_payload['search'] = query
        elif query_type == 'vector_semantic_hybrid':
            request_payload['search'] = query
            request_payload['queryType'] = 'semantic'
            request_payload['semanticConfiguration'] = semantic_configuration_name
    else:
        raise Exception(f"unsupported query type: {query_type}")
    
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    retrieved_docs = requests.post(request_url, json = request_payload, headers = headers, timeout=None)
    if retrieved_docs.status_code == 200:
        return retrieved_docs.json()["value"]
    else:
        raise Exception(f"failed to query search index : {retrieved_docs.json()}")

@tool
def search(queries: str, search_connection: CognitiveSearchConnection, index_name: str, query_type: str, top_k: int, semantic_configuration: str, vector_fields: str, embedding_connection: AzureOpenAIConnection, embedding_model: str):
    semantic_configuration = semantic_configuration if semantic_configuration != "None" else None
    vector_fields = vector_fields if vector_fields != "None" else None
    embedding_model = embedding_model if embedding_model != None else None
                      
    # Do search.
    all_outputs = [search_query_api(
        search_connection['api_base'], 
        search_connection['api_key'], 
        search_connection['api_version'], 
        index_name,
        query_type,
        query, 
        top_k, 
        embedding_connection, 
        embedding_model,
        semantic_configuration,
        vector_fields) for query in get_query_list(queries)]

    included_outputs = []
    while all_outputs and len(included_outputs) < top_k:
        for output in list(all_outputs):
            if len(output) == 0:
                all_outputs.remove(output)
                continue
            value = output.pop(0)
            if value not in included_outputs:
                included_outputs.append(value)
                if len(included_outputs) >= top_k:
                    break
    return included_outputs

