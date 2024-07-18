'''
Sitemap plugin for CKAN
'''

import ckan.plugins as p

from ckan.plugins.toolkit import config, url_for
from ckan.model import Session, Package
from flask import Blueprint, make_response

from lxml import etree
from datetime import date
import json

import ckanext.sitemap.helpers as h

import logging

PURE_NS = "v1.dataset.pure.atira.dk"
PURE = "{%s}" % PURE_NS

PURE_CMNS = "v3.commons.pure.atira.dk"
CMNS = "{%s}" % PURE_CMNS

log = logging.getLogger(__file__)

def render_pure():
    # Consider adding validation here
    schema_file = '/usr/lib/ckan/default/src/ckanext-sitemap/ckanext/sitemap/dataset.xsd'
    xmlschema_doc = etree.parse(schema_file)
    xmlschema = etree.XMLSchema(xmlschema_doc)

    log.error("Hello")
    pkgs = Session.query(Package).filter(Package.type == 'dataset').filter(Package.private != True). \
        filter(Package.state == 'active').all()
    log.debug(pkgs)
    root = etree.Element(PURE + "datasets", nsmap={'v1': PURE_NS, 'v3': PURE_CMNS})
    for pkg in pkgs:
        #log.error(pkg.as_dict())
        dataset = etree.SubElement(root, PURE + 'dataset', attrib={'id': pkg.id, 'type': 'dataset'})

        # Title
        title = etree.SubElement(dataset, PURE + 'title')
        title.text = pkg.title

        # Description
        description = etree.SubElement(dataset, PURE + 'description')
        description.text = pkg.notes

        # DOI
        resource_url = h.getExtrasValue(pkg, 'resource-url')
        if h.isDOI(resource_url):
            doi = etree.SubElement(dataset, PURE + 'DOI')
            doi.text = h.getDOISuffix(resource_url)

        # Available Date
        pubDate = h.getExtrasValue(pkg, 'publication_date')
        dateParts = h.getDateComponents(pubDate)
        availDate = etree.SubElement(dataset, PURE + 'availableDate')
        year = etree.SubElement(availDate, CMNS + 'year')
        year.text = dateParts[0]
        month = etree.SubElement(availDate, CMNS + 'month')
        month.text = dateParts[1]
        day = etree.SubElement(availDate, CMNS + 'day')
        day.text = dateParts[2]

        # Managing Organization
        managingOrg = h.getExtrasValue(pkg, 'resource-support-organization')
        if not managingOrg:
            managingOrg = pkg.organization['name']
        org = etree.SubElement(dataset, PURE + 'managingOrganisation', attrib={'lookupId': managingOrg})

        # Publisher
        publisher = h.getExtrasValue(pkg, 'publisher-standard')
        publisher = json.loads(publisher)[0]
        org = etree.SubElement(dataset, PURE + 'publisher', attrib={'lookupId': publisher})


    content = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='utf-8')

    xmlschema.assertValid(root)

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
        print("pkg: " + pkg)
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

def render_commons():
    f = open('/usr/lib/ckan/default/src/ckanext-sitemap/ckanext/sitemap/commons.xsd')
    content = f.read()
    headers = {'Content-Type': 'text/html; charset=utf-8'}
    return make_response((content, 200, headers))

def render_dataset():
    f = open('/usr/lib/ckan/default/src/ckanext-sitemap/ckanext/sitemap/dataset.xsd')
    content = f.read()
    headers = {'Content-Type': 'text/html; charset=utf-8'}
    return make_response((content, 200, headers))


class SitemapPlugin(p.SingletonPlugin):
    p.implements(p.IBlueprint)
    #p.implements(p.ITemplateHelpers)

    def get_blueprint(self):
        blueprint = Blueprint("sitemap", self.__module__)
        blueprint.add_url_rule("/sitemap.xml", view_func=render_sitemap)
        blueprint.add_url_rule("/pure.xml", view_func=render_pure)
        blueprint.add_url_rule("/commons.xsd", view_func=render_commons)
        blueprint.add_url_rule("/dataset.xsd", view_func=render_dataset)

        # Use this to debug routes
        #blueprint.add_url_rule("/testme", view_func=testme)
        return blueprint
        
#     ## ITemplateHelpers
#
#     def get_helpers(self):
#
#         function_names = (
#             'getExtrasValue',
#             'isDOI',
#         )
#         return _get_module_functions(helpers, function_names)
#
#
# def _get_module_functions(module, function_names):
#     """ Reformat helper function names for get_helpers()
#     """
#     functions = {}
#     for f in function_names:
#         functions[f] = module.__dict__[f]
#
#     return functions