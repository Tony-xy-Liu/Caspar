import time
import requests
import xmltodict    
from typing import Any
import urllib.parse
from .constants import WORKSPACE_ROOT
from .caching import DictCache

# #####################################################################################################################
# utils

def chain_get(d: dict, path: list|str) -> Any:
    if isinstance(path, str): path = path.split(', ')
    todo:list[tuple[dict, int]] = [(d, 0)]
    results = []
    while len(todo) > 0:
        curr, depth = todo.pop()
        if len(curr) == 0: continue
        if depth >= len(path):
            if isinstance(curr, list):
                results += curr
            else: 
                results.append(curr)
            continue
        
        if isinstance(curr, list):
            todo += [(x, depth) for x in curr]
        elif not isinstance(curr, dict):
            assert False, (curr, path[depth-1])
        else:
            todo.append((curr.get(path[depth], {}), depth+1))
    return results if len(results)>0 else None

# #####################################################################################################################
# ncbi

# https://www.ncbi.nlm.nih.gov/account/settings/
# https://www.ncbi.nlm.nih.gov/books/NBK25497/#_chapter2_Usage_Guidelines_and_Requiremen_
with open(WORKSPACE_ROOT.joinpath("secrets/ncbi_apikey")) as f:
    API_KEY = f.readline()

def ncbi_get(action: str, db: str, params: list[tuple[str, str]]):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    url=f"{base_url}/{action}.fcgi?"+"&".join([
        f"api_key={API_KEY}",
        f"db={db}",
    ]+[
        f"{k}={urllib.parse.quote(v)}" for k, v in params
    ])
    with DictCache("ncbi_requests") as request_cache:
        _s = url.index("api_key")
        _e = url.index("&", _s)+1
        ckey = url[:_s]+url[_e:]
        ckey = ckey.replace(base_url, "")
        _cached_r = request_cache.get(ckey)
        if _cached_r is None:
            time.sleep(0.1)
            r = requests.get(url)
            d: dict = xmltodict.parse(r.text)
            if r.status_code != 200: return r.status_code, d
            request_cache[ckey] = dict(status_code = r.status_code, data=d)
        else:
            d: dict = _cached_r["data"]
        return 200, d

def ncbi_search(query: str, db: str, response_type: str="esummary", 
                search_params: list[tuple[str, str]]=list(), 
                response_params: list[tuple[str, str]]=list(), 
                silent: bool=False):
    # db = "biosample", https://www.ncbi.nlm.nih.gov/books/NBK25497/table/chapter2.T._entrez_unique_identifiers_ui/?report=objectonly

    _esearch = "esearch"
    code, d = ncbi_get(_esearch, db, params=[("term", query)]+search_params)
    if code != 200: return _esearch, d

    rdata = d.get('eSearchResult', {})
    ids = rdata.get('IdList', {}).get('Id')
    idcount = int(rdata.get('Count', 0))

    if idcount == 0 or ids is None: return "not found", d
    elif idcount == 1:
        ids = [ids]

    responses: list[dict] = []
    for i, id in enumerate(ids):
        assert id != ""
        if not silent: print(f"\rfetching result {i+1} of {len(ids)}", end="")
        status_code, data = ncbi_get(response_type, db, params=[("id", id)]+response_params)
        if status_code != 200: continue
        responses.append(data)
        
    if len(responses) == 0: return response_type, ids
    return None, responses
