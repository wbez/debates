#!/usr/bin/env python
"""
Example application views.

Note that `render_template` is wrapped with `make_response` in all application
routes. While not necessary for most Flask apps, it is required in the
App Template for static publishing.
"""

import app_config
import logging
import oauth
import os
import parse_doc
import static

from copydoc import CopyDoc
from flask import Flask, make_response, render_template
from flask_cors import CORS, cross_origin
from render_utils import flatten_app_config, make_context
from render_utils import smarty_filter, urlencode_filter
from werkzeug.debug import DebuggedApplication
from oauth import get_document, get_credentials, get_doc

app = Flask(__name__)
app.debug = app_config.DEBUG
CORS(app)

app.add_template_filter(smarty_filter, name='smarty')
app.add_template_filter(urlencode_filter, name='urlencode')

logging.basicConfig(format=app_config.LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(app_config.LOG_LEVEL)


@app.route('/factcheck.html', methods=['GET', 'OPTIONS'])
def _factcheck():
    """
    Liveblog only contains published posts
    """
    get_document(app_config.COPY_GOOGLE_DOC_KEY, app_config.COPY_PATH)

    context = get_factcheck_context()
    return make_response(render_template('factcheck.html', **context))


@app.route('/share.html', methods=['GET', 'OPTIONS'])
def _share():
    """
    Preview contains published and draft posts
    """
    context = get_factcheck_context()
    return make_response(render_template('share.html', **context))


@app.route('/copydoc.html', methods=['GET', 'OPTIONS'])
def _copydoc():
    """
    Example view demonstrating rendering a simple HTML page.
    """
    with open(app_config.TRANSCRIPT_HTML_PATH) as f:
        html = f.read()

    doc = CopyDoc(html)
    context = {
        'doc': doc
    }

    return make_response(render_template('copydoc.html', **context))


@app.route('/child.html')
@oauth.oauth_required
def child():
    """
    Example view demonstrating rendering a simple HTML page.
    """
    context = make_context()

    return make_response(render_template('child.html', **context))


@app.route('/')
@oauth.oauth_required
def index():
    """
    Example view demonstrating rendering a simple HTML page.
    """
    context = make_context()

    return make_response(render_template('parent.html', **context))


app.register_blueprint(static.static)
app.register_blueprint(oauth.oauth)


def get_factcheck_context():
    """
    Get factcheck context
    for production we will reuse a fake g context
    in order not to perform the parsing twice
    """
    from flask import g
    context = flatten_app_config()
    parsed_factcheck_doc = getattr(g, 'parsed_factcheck', None)
    if parsed_factcheck_doc is None:
        logger.debug("did not find parsed_factcheck")
        with open(app_config.TRANSCRIPT_HTML_PATH) as f:
            html = f.read()
        context.update(parse_document(html))
    else:
        logger.debug("found parsed_factcheck in g")
        context.update(parsed_factcheck_doc)
    return context


def parse_document(html):
    doc = CopyDoc(html)
    parsed_document = parse_doc.parse(doc)

    return parsed_document


# Enable Werkzeug debug pages
if app_config.DEBUG:
    wsgi_app = DebuggedApplication(app, evalex=False)
else:
    wsgi_app = app

# Catch attempts to run the app directly
if __name__ == '__main__':
    logging.error('This command has been removed! Run "fab app" instead!')
