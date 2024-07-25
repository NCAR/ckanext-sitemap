'''
Sitemap plugin for CKAN
'''

import ckan.plugins as p

from ckan.plugins.toolkit import config, url_for
from ckan.model import Session, Package
from flask import Blueprint, make_response


from lxml import etree

import logging



def render_pure():
    # Consider adding validation here
    pure_file = '/usr/lib/ckan/PURE_OUTPUT/pure.xml'
    f = open(pure_file, "r")
    content = f.read()

    # Add XML header
    headers = {'Content-Type': 'application/xml; charset=utf-8'}
    return make_response((content, 200, headers))



SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"

XHTML_NS = "http://www.w3.org/1999/xhtml"

def render_sitemap():
    site_url = config.get('ckan.site_url')
    pkgs = Session.query(Package).filter(Package.type == 'dataset').filter(Package.private != True). \
        filter(Package.state == 'active').all()
    log.debug(pkgs)
    root = etree.Element("urlset", nsmap={None: SITEMAP_NS, 'xhtml': XHTML_NS})
    for pkg in pkgs:
        url = etree.SubElement(root, 'url')
        loc = etree.SubElement(url, 'loc')
        pkg_url = url_for('dataset.read', id=pkg.name)
        loc.text = site_url + pkg_url
        lastmod = etree.SubElement(url, 'lastmod')
        lastmod.text = pkg.metadata_modified.strftime('%Y-%m-%d')

    # Add XML header
    content = etree.tostring(root, pretty_print=True, encoding='unicode')
    content = '<?xml version="1.0" encoding="UTF-8"?>\n' + content
    headers = {'Content-Type': 'application/xml; charset=utf-8'}
    return make_response((content, 200, headers))


def testme():
    content = 'Test Me'
    headers = {'Content-Type': 'text/html; charset=utf-8'}
    return make_response((content, 200, headers))


class SitemapPlugin(p.SingletonPlugin):
    p.implements(p.IBlueprint)

    def get_blueprint(self):
        blueprint = Blueprint("sitemap", self.__module__)
        blueprint.add_url_rule("/sitemap.xml", view_func=render_sitemap)
        blueprint.add_url_rule("/pure.xml", view_func=render_pure)
        #blueprint.add_url_rule("/commons.xsd", view_func=render_commons)
        #blueprint.add_url_rule("/dataset.xsd", view_func=render_dataset)

        # Use this to debug routes
        #blueprint.add_url_rule("/testme", view_func=testme)
        return blueprint
        
