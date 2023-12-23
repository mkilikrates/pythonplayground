import os
import json
import urllib3
import logging
import http
import ssl
import asyncio
from aiohttp import BasicAuth
import socket
import backoff
from gql import Client
from gql.dsl import DSLSchema, DSLQuery, DSLFragment, dsl_gql, print_ast
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportQueryError

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
    # Using warning to reduce noise
    # https://gql.readthedocs.io/en/latest/advanced/logging.html
    loglevel = os.environ.get('LOG_LEVEL','WARNING')
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
        http.client.HTTPConnection.debuglevel = 1
        http.client.print = print_to_log
        httplog.addHandler(ch)
        httplog.propagate = True
    else:
        http.client.HTTPConnection.debuglevel = 0
        httplog.addHandler(ch)
        httplog.propagate = False
    return logger

def print_to_log(*args):
    logger.debug(" ".join(args))

async def get_gql_transport(endpoint,access_token):
    logger.warning("Setting up gql transport")
    # certificate
    cert = os.environ.get('CERTIFICATE',None)
    if cert == None:
        ssl_context = True
    elif cert == "False" or cert == "false":
        ssl_context = False
        urllib3.disable_warnings()
    else:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.load_verify_locations(cert)
    if access_token !=None:
        headers={"Authorization": f"Bearer {access_token}"}
    else:
        headers=None
    # Set up the HTTP transport with your access token
    transport = AIOHTTPTransport(
        url=endpoint,
        headers=headers,
        ssl=(ssl_context)
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
        proxyauth=BasicAuth(login=user,password=password)
        transport.auth = proxyauth
    return transport

async def get_gql_client(transport,fetch_schema):
    logger.warning("Setting up gql client")
    # Here wait maximum 5 minutes between connection retries
    try:
        # establish and fetch schema using introspection
        gqlclient = Client(
            transport=transport,
            fetch_schema_from_transport=fetch_schema
        )
    except Exception as e:
        logger.error(f"Error Getting client: {e}")
        gqlclient = 'Failed'
    return gqlclient

async def get_gql_session(client,recon):
    logger.warning("Creating gql session")
    # Here wait maximum 5 minutes between connection retries
    retry_connect = backoff.on_exception(
        backoff.expo,  # wait generator (here: exponential backoff)
        Exception,     # which exceptions should cause a retry (here: everything)
        max_value=300 # max wait time in seconds
    )
    retry_execute = backoff.on_exception(
        backoff.expo,  # wait generator (here: exponential backoff)
        Exception,     # which exceptions should cause a retry (here: everything)
        max_tries=15,
        max_value=120, # max wait time in seconds
        giveup=lambda e: isinstance(e, TransportQueryError)
    )
    try:
        # establish and fetch schema using introspection
        gqlsession = await client.connect_async(
            reconnecting=recon,
            retry_connect=retry_connect,
            retry_execute=retry_execute
        )
    except Exception as e:
        logger.error(f"Error Getting client: {e}")
        gqlsession = 'Failed'
    return gqlsession

def query_continents(ds):
    logger.warning("Creating gql query for continents")
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
    logger.warning(f"Creating gql query for country code {code}")
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
    logger.warning(f"Creating gql query for countries on continent code {code}")
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

async def execute_query(query, session):
    logger.warning("Executing gql query")
    # Execute the query
    try:
        result = await session.execute(query)
    except Exception as e:
        logger.error(f"Error Executing query : {e}\nError: {json.dumps(result['errors'])}\nHeaders: {result['headers']}")
        result = "Failed"
    return result

#################################### variables on Environment #####################################################################
# export USR='username' # proxy username authentication
# export PSW='password'
# export SET_PROXY='http://myproxy.com:3128'
###################################################################################################################################

async def main():
    config()
    global logger
    logger = set_logger()
    endpoint = "https://countries.trevorblades.com/graphql"
    # Get transport
    transport = await get_gql_transport(endpoint,None)
    gql_client = await get_gql_client(transport,True)
    gql_session = await get_gql_session(gql_client,True)
    # assert await gqlsession.schema is not None
    # Instantiate the root of the DSL Schema as ds
    ds = DSLSchema(gql_client.schema)
    # simple query
    query = query_continents(ds)
    if query == "Failed":
        await gql_session.close_async()
        await transport.close()
    else:
        logger.debug(f"QUERY DATA: {print_ast(query)}")
        result = await execute_query(query, gql_session)
        if query == "Failed":
            await gql_session.close_async()
            await transport.close()
        else:
            logger.debug(f"Success : {json.dumps(result)}")
            print(f"Result: {json.dumps(result,indent=2)}")
    # query with variables
    countrycode="IE"
    query = query_contry_by_code(ds,countrycode)
    if query == "Failed":
        logger.warning("Closing gql client session")
        await gql_client.close_async()
        logger.warning("Closing gql transport")
        await transport.close()
    else:
        logger.debug(f"QUERY DATA: {print_ast(query)}")
        result = await execute_query(query, gql_session)
        if query == "Failed":
            logger.warning("Closing gql client session")
            await gql_client.close_async()
            logger.warning("Closing gql transport")
            await transport.close()
        else:
            logger.debug(f"Success : {json.dumps(result)}")
            print(f"Result: {json.dumps(result,indent=2)}")
    # query with fragment
    continentcode = 'EU'
    query=query_contries_on_continent(ds,continentcode)
    if query == "Failed":
            logger.warning("Closing gql client session")
            await gql_client.close_async()
            logger.warning("Closing gql transport")
            await transport.close()
    else:
        logger.debug(f"QUERY DATA: {print_ast(query)}")
        result = await execute_query(query, gql_session)
        if query == "Failed":
            logger.warning("Closing gql client session")
            await gql_client.close_async()
            logger.warning("Closing gql transport")
            await transport.close()
        else:
            logger.debug(f"Success : {json.dumps(result)}")
            print(f"Result: {json.dumps(result,indent=2)}")
    logger.warning("Closing gql client session")
    await gql_client.close_async()
    logger.warning("Closing gql transport")
    await transport.close()

if __name__ == "__main__":
    asyncio.run(main())
