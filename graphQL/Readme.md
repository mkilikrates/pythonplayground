# GraphQL Client KT Session

This is some examples and code for using graphql client

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Description](#description)
- [Explorer](#explorer)
  - [Sample Queries](#sample-queries)
    - [Simple Query](#simple-query)
    - [Query with arguments](#query-with-arguments)
    - [Using Variables](#using-variables)
    - [Fragments](#fragments)
- [Python GQL](#python-gql)
  - [Dynamic Queries](#dynamic-queries)
    - [Dynamic Simple Query](#dynamic-simple-query)
    - [Dynamic Query with Variables](#dynamic-query-with-variables)
    - [Dynamic Query using Fragments](#dynamic-query-using-fragments)
  - [Logging and Cavets](#logging-and-cavets)
    - [Using Virtual Environment](#using-virtual-environment)
    - [Queries Commented on the code](#queries-commented-on-the-code)
    - [Assynchronous Queries](#asynchronous-queries)
- [Useful Links](#useful-links)
- [Help](#help)
- [Thanks to](#thanks-to)
- [Version History](#version-history)

## Description

[GraphQL](https://graphql.org/) is a query language for APIs.

One of the main advantage of using graphql over the traditional rest-api is for instance when comparing response for [list repositories on github rest-api](https://docs.github.com/en/enterprise-cloud@latest/rest/repos/repos?apiVersion=2022-11-28#list-organization-repositories) you can see that the response for each reposity will bring all details.

Others API like [Bitbucket Projects](https://docs.atlassian.com/bitbucket-server/rest/4.1.0/bitbucket-rest.html#idp2128896) may bring little information so you may need additional queries for getting repositories inside of this project for instance.

Using [GraphQL API](https://docs.github.com/en/enterprise-cloud@latest/graphql/reference/objects#repository) you can select what information you want to receive as well in some cases getting additional information in a single query using fragments.

Github highlights what to consider when [migrationg from REST to GraphQL](https://docs.github.com/en/enterprise-cloud@latest/graphql/guides/migrating-from-rest-to-graphql)

There are several [public endpoints](https://github.com/graphql-kit/graphql-apis) that you can use for learning.

For this KT Session the endpoint is [Coutries API](https://countries.trevorblades.com/) by [Trevor Blades](https://trevorblades.com/#about)

Since we are dealing with public APIs we are not covering doing changes (mutations), only queries.

## Explorer

[Explorer](https://countries.trevorblades.com/graphql) is a "graphical interactive in-browser GraphQL IDE" that that includes docs, syntax highlighting, and validation errors.

For details on concepts please look at [Introduction to GraphQL](https://graphql.org/learn/) or [Main Concepts](https://graphql-docs.fmr.com/docs/learning/concepts/)

### Sample Queries

These are some simple queries

#### Simple Query

Get list of continents

- Request

```graphql
query GetContinents {
  continents{
    name
    code
  }
}
```

- Response

```json
{
  "data": {
    "continents": [
      {
        "name": "Africa",
        "code": "AF"
      },
      {
        "name": "Antarctica",
        "code": "AN"
      },
      {
        "name": "Asia",
        "code": "AS"
      },
      {
        "name": "Europe",
        "code": "EU"
      },
      {
        "name": "North America",
        "code": "NA"
      },
      {
        "name": "Oceania",
        "code": "OC"
      },
      {
        "name": "South America",
        "code": "SA"
      }
    ]
  }
}
```

#### Query with arguments

Get a County information based on Country Code "IE"

- Request

```graphql
query GetCountry {
  country(code: "IE") {
    continent{
      name
    }
    name
    native
    capital
    emoji
    currency
    languages {
      code
      name
    }
  }
}
```

- Response

```json
{
  "data": {
    "country": {
      "continent": {
        "name": "Europe"
      },
      "name": "Ireland",
      "native": "Éire",
      "capital": "Dublin",
      "emoji": "🇮🇪",
      "currency": "EUR",
      "languages": [
        {
          "code": "ga",
          "name": "Irish"
        },
        {
          "code": "en",
          "name": "English"
        }
      ]
    }
  }
}
```

#### Using Variables

Get list of Countries from continent passed on variable

- Variables

```json
{
  "continentCode": "EU"
}
```

- Request

```graphql
query GetContinents (
  $continentCode: String!
){
  continents(filter:{code: {eq: $continentCode}}){
    name
    code
    countries{
      name
      capital
    }
  }
}
```

- Response

```json
{
  "data": {
    "continents": [
      {
        "name": "Europe",
        "code": "EU",
        "countries": [
          {
            "name": "Andorra",
            "capital": "Andorra la Vella"
          },
          {
            "name": "Albania",
            "capital": "Tirana"
          },
          {
            "name": "Austria",
            "capital": "Vienna"
          },
          {
            "name": "Åland",
            "capital": "Mariehamn"
          },
          {
            "name": "Bosnia and Herzegovina",
            "capital": "Sarajevo"
          },
          {
            "name": "Belgium",
            "capital": "Brussels"
          },
          {
            "name": "Bulgaria",
            "capital": "Sofia"
          },
          {
            "name": "Belarus",
            "capital": "Minsk"
          },
          {
            "name": "Switzerland",
            "capital": "Bern"
          },
          {
            "name": "Cyprus",
            "capital": "Nicosia"
          },
          {
            "name": "Czech Republic",
            "capital": "Prague"
          },
          {
            "name": "Germany",
            "capital": "Berlin"
          },
          {
            "name": "Denmark",
            "capital": "Copenhagen"
          },
          {
            "name": "Estonia",
            "capital": "Tallinn"
          },
          {
            "name": "Spain",
            "capital": "Madrid"
          },
          {
            "name": "Finland",
            "capital": "Helsinki"
          },
          {
            "name": "Faroe Islands",
            "capital": "Tórshavn"
          },
          {
            "name": "France",
            "capital": "Paris"
          },
          {
            "name": "United Kingdom",
            "capital": "London"
          },
          {
            "name": "Guernsey",
            "capital": "St. Peter Port"
          },
          {
            "name": "Gibraltar",
            "capital": "Gibraltar"
          },
          {
            "name": "Greece",
            "capital": "Athens"
          },
          {
            "name": "Croatia",
            "capital": "Zagreb"
          },
          {
            "name": "Hungary",
            "capital": "Budapest"
          },
          {
            "name": "Ireland",
            "capital": "Dublin"
          },
          {
            "name": "Isle of Man",
            "capital": "Douglas"
          },
          {
            "name": "Iceland",
            "capital": "Reykjavik"
          },
          {
            "name": "Italy",
            "capital": "Rome"
          },
          {
            "name": "Jersey",
            "capital": "Saint Helier"
          },
          {
            "name": "Liechtenstein",
            "capital": "Vaduz"
          },
          {
            "name": "Lithuania",
            "capital": "Vilnius"
          },
          {
            "name": "Luxembourg",
            "capital": "Luxembourg"
          },
          {
            "name": "Latvia",
            "capital": "Riga"
          },
          {
            "name": "Monaco",
            "capital": "Monaco"
          },
          {
            "name": "Moldova",
            "capital": "Chișinău"
          },
          {
            "name": "Montenegro",
            "capital": "Podgorica"
          },
          {
            "name": "North Macedonia",
            "capital": "Skopje"
          },
          {
            "name": "Malta",
            "capital": "Valletta"
          },
          {
            "name": "Netherlands",
            "capital": "Amsterdam"
          },
          {
            "name": "Norway",
            "capital": "Oslo"
          },
          {
            "name": "Poland",
            "capital": "Warsaw"
          },
          {
            "name": "Portugal",
            "capital": "Lisbon"
          },
          {
            "name": "Romania",
            "capital": "Bucharest"
          },
          {
            "name": "Serbia",
            "capital": "Belgrade"
          },
          {
            "name": "Russia",
            "capital": "Moscow"
          },
          {
            "name": "Sweden",
            "capital": "Stockholm"
          },
          {
            "name": "Slovenia",
            "capital": "Ljubljana"
          },
          {
            "name": "Svalbard and Jan Mayen",
            "capital": "Longyearbyen"
          },
          {
            "name": "Slovakia",
            "capital": "Bratislava"
          },
          {
            "name": "San Marino",
            "capital": "City of San Marino"
          },
          {
            "name": "Ukraine",
            "capital": "Kyiv"
          },
          {
            "name": "Vatican City",
            "capital": "Vatican City"
          },
          {
            "name": "Kosovo",
            "capital": "Pristina"
          }
        ]
      }
    ]
  }
}
```

#### Fragments

Get details from each country in a list of countries in a Continent

- Request

```graphql
fragment CountryInfo on Country {
  code
  name
  capital
  currency
}
query GetCountriesonContinent{
  continent(code: "OC") {
    code
    name
    countries {
      ...CountryInfo
    }
  }
}
```

- Response

```json
{
  "data": {
    "continent": {
      "code": "OC",
      "name": "Oceania",
      "countries": [
        {
          "code": "AS",
          "name": "American Samoa",
          "capital": "Pago Pago",
          "currency": "USD"
        },
        {
          "code": "AU",
          "name": "Australia",
          "capital": "Canberra",
          "currency": "AUD"
        },
        {
          "code": "CK",
          "name": "Cook Islands",
          "capital": "Avarua",
          "currency": "NZD"
        },
        {
          "code": "FJ",
          "name": "Fiji",
          "capital": "Suva",
          "currency": "FJD"
        },
        {
          "code": "FM",
          "name": "Micronesia",
          "capital": "Palikir",
          "currency": "USD"
        },
        {
          "code": "GU",
          "name": "Guam",
          "capital": "Hagåtña",
          "currency": "USD"
        },
        {
          "code": "KI",
          "name": "Kiribati",
          "capital": "South Tarawa",
          "currency": "AUD"
        },
        {
          "code": "MH",
          "name": "Marshall Islands",
          "capital": "Majuro",
          "currency": "USD"
        },
        {
          "code": "MP",
          "name": "Northern Mariana Islands",
          "capital": "Saipan",
          "currency": "USD"
        },
        {
          "code": "NC",
          "name": "New Caledonia",
          "capital": "Nouméa",
          "currency": "XPF"
        },
        {
          "code": "NF",
          "name": "Norfolk Island",
          "capital": "Kingston",
          "currency": "AUD"
        },
        {
          "code": "NR",
          "name": "Nauru",
          "capital": "Yaren",
          "currency": "AUD"
        },
        {
          "code": "NU",
          "name": "Niue",
          "capital": "Alofi",
          "currency": "NZD"
        },
        {
          "code": "NZ",
          "name": "New Zealand",
          "capital": "Wellington",
          "currency": "NZD"
        },
        {
          "code": "PF",
          "name": "French Polynesia",
          "capital": "Papeetē",
          "currency": "XPF"
        },
        {
          "code": "PG",
          "name": "Papua New Guinea",
          "capital": "Port Moresby",
          "currency": "PGK"
        },
        {
          "code": "PN",
          "name": "Pitcairn Islands",
          "capital": "Adamstown",
          "currency": "NZD"
        },
        {
          "code": "PW",
          "name": "Palau",
          "capital": "Ngerulmud",
          "currency": "USD"
        },
        {
          "code": "SB",
          "name": "Solomon Islands",
          "capital": "Honiara",
          "currency": "SBD"
        },
        {
          "code": "TK",
          "name": "Tokelau",
          "capital": "Fakaofo",
          "currency": "NZD"
        },
        {
          "code": "TL",
          "name": "East Timor",
          "capital": "Dili",
          "currency": "USD"
        },
        {
          "code": "TO",
          "name": "Tonga",
          "capital": "Nuku'alofa",
          "currency": "TOP"
        },
        {
          "code": "TV",
          "name": "Tuvalu",
          "capital": "Funafuti",
          "currency": "AUD"
        },
        {
          "code": "UM",
          "name": "U.S. Minor Outlying Islands",
          "capital": null,
          "currency": "USD"
        },
        {
          "code": "VU",
          "name": "Vanuatu",
          "capital": "Port Vila",
          "currency": "VUV"
        },
        {
          "code": "WF",
          "name": "Wallis and Futuna",
          "capital": "Mata-Utu",
          "currency": "XPF"
        },
        {
          "code": "WS",
          "name": "Samoa",
          "capital": "Apia",
          "currency": "WST"
        }
      ]
    }
  }
}
```

## Python GQL

[GQL](https://github.com/graphql-python/gql) is a [GraphQL](https://graphql.org/) Client implementation compatible with the spec.

It supports multiple [transports](https://gql.readthedocs.io/en/stable/transports/index.html#transports) to communicate with the backend.

It has [Schema validation](https://gql.readthedocs.io/en/stable/usage/validation.html) capabilities for both local schemas or fetch using [introspection query](https://graphql.org/learn/introspection/)

It allows to create GraphQL queries dynamically instead of providing the GraphQL queries as a Python String.

### Dynamic Queries

These are some simple query examples

#### Dynamic Simple Query

Get list of continents

```python
query = dsl_gql(
    DSLQuery(
        GetContinents=ds.Query.continents.select(
            ds.Continent.code,
            ds.Continent.name
        )
    )
)
```

on the [graphQL-demo.py](graphQL-demo.py) query_continents

#### Dynamic Query with Variables

```python
code="IE"
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
```

on the [graphQL-demo.py](graphQL-demo.py) query_contry_by_code

#### Dynamic Query using Fragments

```python
continentcode = 'OC'
class DSLVariableDefinitions:
    continentcode = continentcode
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
```

on the [graphQL-demo.py](graphQL-demo.py) query_contries_on_continent

### Logging and Cavets

These are some simple query examples

This script when executed in DEBUG mode, will generated detail logs:

- HTTP(s) transactions
- Schema
- queries

To enable DEBUG:

```bash
export LOG_LEVEL='DEBUG'
```

#### Using virtual environment

Recommend to use it

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install --upgrade -r requirements.txt
python graphQL-demo.py
```

#### Queries Commented on the code

Since this is just a demo session, the idea is execute one example each time, so you must comment / uncomment the query you intend to use

```python
# simple query
# query = query_continents(ds)
# query with variables
# countrycode="IE"
# query = query_contry_by_code(ds,countrycode)
# query with fragment  <<<-------------------------------- This is the active query
continentcode = 'EU'
query=query_contries_on_continent(ds,continentcode)
```

#### Asynchronous queries

Sometimes you want to have a single permanent reconnecting async session to a GraphQL backend, and that can be difficult to manage manually with the async with client as session syntax.

It is now possible to have a single reconnecting session using the [connect_async](https://gql.readthedocs.io/en/stable/advanced/async_permanent_session.html) method of Client with a reconnecting=True argument.

For instance, in a single session you can make several queries like you see in the [async-code](./src/async/app-demo.py).

## Useful Links

- [cheat sheet](https://github.com/sogko/graphql-schema-language-cheat-sheet)
- [GQL docs](https://gql.readthedocs.io/en/stable/)
- [Github GraphQL doc](https://docs.github.com/en/enterprise-cloud@latest/graphql)
- [Github GraphQL Explorer](https://docs.github.com/en/enterprise-cloud@latest/graphql/overview/explorer)

## Help

Any advice for common problems or issues.

## Version History

- 0.1
  - Initial Release
