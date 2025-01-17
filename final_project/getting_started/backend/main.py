from fastapi.responses import HTMLResponse
from config import INDEX_NAME
from utils import get_es_client

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import json

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

@app.get('/api/v1/regular_search')
async def search(search_query: str, skip: int = 0, limit: int = 10) -> dict:
    es = get_es_client(max_retries=5, sleep_time=5)
    response = es.search(
        index=INDEX_NAME,
        body={
            'query': {
                'multi_match': {
                    'query': search_query,
                    'fields': ['title', 'explanation']
                }
            },
            'from': skip,
            'size': limit
        },
        filter_path=['hits.hits._source, hits.hits_score']
    )
    hits=response['hits']['hits']
    return {
        'hits': hits 
    }

@app.get('/api/v1/get_docs_per_year_count/')
async def get_docs_per_year_count(search_query: str) -> dict:
    try:
        es = get_es_client()
        query = {
            'bool': {
                'must': [
                    {
                        'multi_match': {
                            'query': search_query,
                            'fields': ['title', 'explanation']
                        }
                    }
                ]
            }
        }

        response = es.search(
            index=INDEX_NAME,
            body={
                'query': query,
                'aggs': {
                    'docs_per_year': {
                        'date_histogram': {
                            'field': 'date',
                            'calendar_interval': 'year', # Group by year
                            'format': 'yyyy' # Format of the year in the response
                        }
                    }
                }
            },
            filter_path=['aggregations.docs_per_year']
        )
        return {
            'docs_per_year': extract_docs_per_year(response)
        }
    except Exception as e:
        return HTMLResponse(content=str(e), status_code=500)

def extract_docs_per_year(response: dict) -> dict:
    aggregations = response.get('aggregations', {})
    docs_per_year = aggregations.get('docs_per_year', {})
    buckets = docs_per_year.get('buckets', {})
    return {
        bucket['key_as_string']: bucket['doc_count'] for bucket in buckets
    }