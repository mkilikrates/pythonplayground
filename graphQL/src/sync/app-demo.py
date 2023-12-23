import os
import json
import urllib3
import logging
import http
from requests.auth import HTTPProxyAuth
import socket

from gql import Client, utilities
from gql.dsl import DSLSchema, DSLQuery, DSLFragment, dsl_gql, print_ast
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.requests import log as requests_logger

def config():
    # set keepalive
    urllib3.connectionpool.HTTPConnection.default_socket_options = (
        urllib3.connectionpool.HTTPConnection.default_socket_options + [
            (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
            (socket.SOL_TCP, socket.TCP_KEEPIDLE, 45),
            (socket.SOL_TCP, socket.TCP_KEEPINTVL, 10),
            (socket.SOL_TCP, socket.TCP_KEEPCNT, 6)
        ]
    )

def set_logger():
    logfmt = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    logdatefmt = "%m-%d-%Y %H:%M:%S"
    logname = (os.path.basename(__file__)).split('.')
    loglevel = os.environ.get('LOG_LEVEL','INFO')
    logging.basicConfig(
        filename=f"{logname[0]}.log",
        format=logfmt,
        datefmt=logdatefmt,
        filemode='a',
        level=loglevel
    )
    logger = logging.getLogger()
    # http logging
    httplog = logging.getLogger('urllib3')
    ch = logging.StreamHandler()
    logger.setLevel(loglevel)
    ch.setLevel(loglevel)
    if loglevel == 'DEBUG':
        requests_logger.setLevel(loglevel)
        http.client.HTTPConnection.debuglevel = 1
        http.client.print = print_to_log
        httplog.addHandler(ch)
        httplog.propagate = True
    else:
        requests_logger.setLevel('WARNING')
        http.client.HTTPConnection.debuglevel = 0
        httplog.addHandler(ch)
        httplog.propagate = False
    return logger

def print_to_log(*args):
    logger.debug(" ".join(args))

def get_gql_transport(endpoint,access_token):
    # certificate
    cert = os.environ.get('CERTIFICATE',None)
    if cert == None:
        certverify = True
    elif cert == "False" or cert == "false":
        certverify = False
        urllib3.disable_warnings()
    else:
        certverify = cert
    if access_token !=None:
        headers={"Authorization": f"Bearer {access_token}"}
    else:
        headers=None
    # Set up the HTTP transport with your access token
    # https://gql.readthedocs.io/en/latest/modules/transport_requests.html
    transport = RequestsHTTPTransport(
        url=endpoint,
        headers=headers,
        verify=certverify,
        retries=15,
        timeout=120,
        method='POST',
        use_json=True
    )
    # set proxy different from environment
    prox = os.environ.get('SET_PROXY',None)
    if prox != None:
        proxies = {
            "http":f"{prox}",
            "https":f"{prox}",
            "no":f"{os.environ.get('no_proxy',None)}"
        }
        transport.proxies = proxies
    # Add Proxy authentication
    user = os.environ.get('USR',None)
    password = os.environ.get('PSW',None)
    if user != None and password != None:
        proxyauth=HTTPProxyAuth(username=user,password=password)
        transport.auth = proxyauth
    return transport

def query_continents(ds):
    try:
        query = dsl_gql(
            DSLQuery(
                GetContinents=ds.Query.continents.select(
                    ds.Continent.code,
                    ds.Continent.name
                )
            )
        )
    except Exception as e:
        logger.error(f"Error Generating query : {e}")
        query = "Failed"
    # else:
    return query

def query_contry_by_code(ds,code):
    try:
        class DSLVariableDefinitions:
            countrycode = code
        query = dsl_gql(
            DSLQuery(
                GetCountryByCode=ds.Query.country.args(
                    code=DSLVariableDefinitions.countrycode
                ).select(
                    ds.Country.continent.select(
                        ds.Continent.name
                    ),
                    ds.Country.name,
                    ds.Country.capital,
                    ds.Country.currency,
                    ds.Country.languages.select(
                        ds.Language.code,
                        ds.Language.name
                    )
                )
            )
        )
    except Exception as e:
        logger.error(f"Error Generating query : {e}")
        query = "Failed"
    # else:
    return query

def query_contries_on_continent(ds,code):
    try:
        class DSLVariableDefinitions:
            continentcode = code
        countryinfo = DSLFragment("CountryInfo")
        countryinfo.on(ds.Country)
        countryinfo.select(
            ds.Country.code,
            ds.Country.name,
            ds.Country.capital,
            ds.Country.currency
        )
        query_with_fragment = DSLQuery(
            GetCountriesonContinent=ds.Query.continent.args(
                code=DSLVariableDefinitions.continentcode
            ).select(
                ds.Continent.code,
                ds.Continent.name,
                ds.Continent.countries.select(
                    countryinfo
                )
            )
        )
        query = dsl_gql(
            countryinfo,
            query_with_fragment
        )
    except Exception as e:
        logger.error(f"Error Generating query : {e}")
        query = "Failed"
    # else:
    return query

def execute_query(query, session):
    # Execute the query
    try:
        result = session.execute(query)
    except Exception as e:
        logger.error(f"Error Executing query : {e}\nError: {json.dumps(result['errors'])}\nHeaders: {result['headers']}")
        result = "Failed"
    return result

#################################### variables on Environment #####################################################################
# export USR='username' # proxy username authentication
# export PSW='password'
# export SET_PROXY='http://my.proxy. com: 3128'
# export CERTIFICATE='False'
# export LOG_LEVEL='INFO' # use DEBUG to log schema, queries and http request/responses
###################################################################################################################################

if __name__ == "__main__":
    config()
    logger = set_logger()
    endpoint = "https://countries.trevorblades.com/graphql"
    # Get transport
    transport = get_gql_transport(endpoint,None)
    try:
        # establish connection and fetch schema using introspection
        gqlclient = Client(transport=transport, fetch_schema_from_transport=True)
    except Exception as e:
        logger.error(f"Error Getting client: {e}")
        transport.close()
    else:
        try:
            with gqlclient as session:
                assert gqlclient.schema is not None
                schema = utilities.get_introspection_query_ast(gqlclient.schema)
                logger.debug(f"SCHEMA: {print_ast(schema)}")
                # Instantiate the root of the DSL Schema as ds
                ds = DSLSchema(gqlclient.schema)
                # simple query
                # query = query_continents(ds)
                # query with variables
                # countrycode="IE"
                # query = query_contry_by_code(ds,countrycode)
                # query with fragment
                continentcode = 'EU'
                query=query_contries_on_continent(ds,continentcode)
                if query == "Failed":
                    gqlclient.close_sync()
                    transport.close()
                else:
                    logger.debug(f"QUERY DATA: {print_ast(query)}")
                    result = execute_query(query, session)
                    if query == "Failed":
                        gqlclient.close_sync()
                        transport.close()
                    else:
                        logger.debug(f"Success : {json.dumps(result)}")
        except Exception as e:
            logger.error(f"Error on client: {e}")
            gqlclient.close_sync()
        finally:
            transport.close()
            print(f"Result: {json.dumps(result,indent=2)}")
