import os
import sys
import json
import csv
import urllib3
import socket
import logging
import http
import requests
from requests.auth import HTTPProxyAuth
from gql import Client, gql
from gql.dsl import DSLSchema, DSLQuery, dsl_gql
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.requests import log as requests_logger
from datetime import datetime
import re
from urllib.parse import urlparse,unquote

#################################### variables on Environment #####################################################################
# export USR='username' # proxy authentication
# export PSW='password' # proxy authentication
# export LOG_LEVEL='INFO'
# export GITHUB_TOKEN='<>' # https://docs.github.com/en/graphql/guides/forming-calls-with-graphql#authenticating-with-graphql
###################################################################################################################################

# keep alive
urllib3.connectionpool.HTTPConnection.default_socket_options = (
    urllib3.connectionpool.HTTPConnection.default_socket_options + [
        (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
        (socket.SOL_TCP, socket.TCP_KEEPIDLE, 45),
        (socket.SOL_TCP, socket.TCP_KEEPINTVL, 10),
        (socket.SOL_TCP, socket.TCP_KEEPCNT, 6)
    ]
)
#logger
logfmt = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
logdatefmt = "%m-%d-%Y %H:%M:%S"
logging.basicConfig(
    filename="app.log",
    format=logfmt,
    datefmt=logdatefmt,
    filemode='a'
)
loglevel = os.environ.get('LOG_LEVEL','INFO')
logger = logging.getLogger()
# print log
def print_to_log(*args):
    logger.debug(" ".join(args))

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

retries=5

user = os.environ.get('USR',None)
password = os.environ.get('PSW',None)

# certificate
cert = os.environ.get('CERTIFICATE',None)
if cert == None:
    certverify = True
elif cert == False:
    certverify = False
    urllib3.disable_warnings()
else:
    certverify = cert

baseurl = 'https://api.github.com/graphql'

token = os.environ.get('GITHUB_TOKEN',None)

if token == None:
    sys.exit("Github Token not found. Exiting...")

headers = {
    "Authorization": f"Bearer {token}"
}

cookies = {}

# set transport http
transport = RequestsHTTPTransport(
    url=baseurl,
    headers=headers,
    verify=certverify,
    retries=retries,
    cookies=cookies,
    method='POST',
    use_json=True
)

# set proxy different from environment
prox = os.environ.get('SET_PROXY',None)
if prox != None:
    proxies = {
        "http":f"{prox}",
        "https":f"{prox}"
    }
    transport.proxies = proxies

# Add Proxy authentication
if user != None and password != None:
    proxyauth=HTTPProxyAuth(username=user,password=password)
    transport.auth = proxyauth

#https://gql.readthedocs.io/en/latest/usage/variables.html
params = {}

client = Client(transport=transport, fetch_schema_from_transport=True)

# github query doc - https://docs.github.com/en/graphql/reference/queries

result = {}
with client as session:
    assert client.schema is not None
    # Instantiate the root of the DSL Schema as ds
    ds = DSLSchema(client.schema)
    # Create the query using dynamically generated attributes from ds
    query = dsl_gql(
        DSLQuery(
            Login=ds.Query.viewer.select(
                ds.User.login
            ),
            Repository=ds.Query.viewer.select(
                ds.User.repositories(
                    first=100
                ).select(
                    ds.RepositoryConnection.nodes.select(
                        ds.Repository.name,
                        ds.Repository.url,
                        ds.Repository.visibility
                    )
                )
            ),
            RateLimit=ds.Query.rateLimit.select(
                ds.RateLimit.cost,
                ds.RateLimit.limit,
                ds.RateLimit.nodeCount,
                ds.RateLimit.remaining,
                ds.RateLimit.resetAt,
                ds.RateLimit.used
            )
        )
    )

    result = session.execute(query)
    logger.debug(f"Success : {json.dumps(result)}")
for repo in result['Repository']['repositories']['nodes']:
    print(f"Repository\n Name: {repo['name']}\n URL: {repo['url']}\n Visibility: {repo['visibility']}\n")
print(f"Rate Limits:\n Cost: {result['RateLimit']['cost']}\n Limit: {result['RateLimit']['limit']}\n Used: {result['RateLimit']['used']}\n Remaining: {result['RateLimit']['remaining']}\n ResetAt: {result['RateLimit']['resetAt']}\n")