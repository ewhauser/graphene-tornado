from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from typing import Optional

import graphene
import pytest
import tornado
from graphene import ObjectType
from graphene import Schema
from graphql import GraphQLResolveInfo
from tornado.escape import to_unicode
from tornado.ioloop import IOLoop

from examples.example import ExampleApplication
from graphene_tornado.tests.http_helper import HttpHelper
from graphene_tornado.tests.test_graphql import response_json
from graphene_tornado.tests.test_graphql import url_string
from graphene_tornado.tornado_graphql_handler import TornadoGraphQLHandler

GRAPHQL_HEADER = {"Content-Type": "application/graphql"}
FORM_HEADER = {"Content-Type": "application/x-www-form-urlencoded"}


class QueryRoot(ObjectType):

    thrower = graphene.String(required=True)
    request = graphene.String(required=True)
    test = graphene.String(who=graphene.String())

    def resolve_thrower(self, info):
        raise Exception("Throws!")

    def resolve_request(self, info: GraphQLResolveInfo) -> str:
        return to_unicode(info.context.arguments["q"][0])

    def resolve_test(self, info: GraphQLResolveInfo, who: Optional[str] = None) -> str:
        return "Hello %s" % (who or "World")


class MutationRoot(ObjectType):
    write_test = graphene.Field(QueryRoot)

    def resolve_write_test(self, info: GraphQLResolveInfo) -> QueryRoot:
        return QueryRoot()


schema = Schema(query=QueryRoot, mutation=MutationRoot)


class SimpleApplication(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r'/graphql', TornadoGraphQLHandler, dict(graphiql=True, schema=schema)),
            (r'/graphql/batch', TornadoGraphQLHandler, dict(graphiql=True, schema=schema, batch=True)),
            (r'/graphql/graphiql', TornadoGraphQLHandler, dict(graphiql=True, schema=schema))
        ]
        tornado.web.Application.__init__(self, handlers)


if __name__ == '__main__':
    app = ExampleApplication()
    app.listen(5000)
    IOLoop.instance().start()


@pytest.fixture
def app():
    return ExampleApplication()


@pytest.fixture
def http_helper(http_client, base_url):
    return HttpHelper(http_client, base_url)


@pytest.mark.gen_test
def test_allows_get_with_query_param(http_helper):
    response = yield http_helper.get(url_string(query="{test}"), headers=GRAPHQL_HEADER)

    assert response.code == 200
    assert response_json(response) == {"data": {"test": "Hello World"}}

