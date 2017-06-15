# -*- coding: utf-8 -*-
from App.config import getConfiguration
from collective.themesitesetup.interfaces import NO
from collective.themesitesetup.interfaces import PLUGIN_NAME
from collective.themesitesetup.interfaces import YES
from ConfigParser import SafeConfigParser
from io import BytesIO
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.plugins.utils import getPlugins
from plone.resource.manifest import MANIFEST_FILENAME
from polib import pofile
from zope.app.i18n.messagecatalog import MessageCatalog
from zope.globalrequest import getRequest
import tarfile

try:
    from plone.app.theming.interfaces import IThemingPolicy
    CACHE = True
except ImportError:
    CACHE = False


def cache(key):
    def wrapper(func):
        def cached(*args, **kwargs):
            if not CACHE or getConfiguration().debug_mode:
                return func(*args, **kwargs)

            request = getRequest()
            policy = IThemingPolicy(request)
            cache_ = policy.getCache()
            if not hasattr(cache_, 'collective.themesitesetup'):
                setattr(cache_, 'collective.themesitesetup', {})
            cache_ = getattr(cache_, 'collective.themesitesetup')

            if callable(key):
                key_ = key(*args)
            else:
                key_ = key

            if key_ not in cache_:
                cache_[key_] = func(*args, **kwargs)
            return cache_[key_]

        return cached
    return wrapper


# This is copied from p.a.theming.plugins.utils to get uncached data
# noinspection PyPep8Naming
def getPluginSettings(themeDirectory, plugins=None):
    """Given an IResourceDirectory for a theme, return the settings for the
    given list of plugins (or all plugins, if not given) provided as a list
    of (name, plugin) pairs.

    Returns a dict of dicts, with the outer dict having plugin names as keys
    and containing plugins settings (key/value pairs) as values.
    """

    if plugins is None:
        plugins = getPlugins()

    # noinspection PyPep8Naming
    manifestContents = {}

    if themeDirectory.isFile(MANIFEST_FILENAME):
        parser = SafeConfigParser()
        fp = themeDirectory.openFile(MANIFEST_FILENAME)

        try:
            parser.readfp(fp)
            for section in parser.sections():
                manifestContents[section] = {}

                for name, value in parser.items(section):
                    manifestContents[section][name] = value

        finally:
            try:
                fp.close()
            except AttributeError:
                pass

    pluginSettings = {}
    for name, plugin in plugins:
        pluginSettings[name] = manifestContents.get("%s:%s" % (THEME_RESOURCE_NAME, name), {})  # noqa

    return pluginSettings


# noinspection PyPep8Naming
def getSettings(themeDirectory):
    settings = getPluginSettings(themeDirectory, plugins=[(PLUGIN_NAME, None)])
    return settings.get(PLUGIN_NAME) or {}


# noinspection PyPep8Naming
def isEnabled(settings):
    return ((settings.get('enabled') or '').lower() not in NO and
            (settings.get('disabled') or '').lower() not in YES)


# noinspection PyPep8Naming
def overwriteModels(settings):
    return ((settings.get('models-overwrite') or '').lower() in YES or
            (settings.get('models-override') or '').lower() in YES)


# noinspection PyPep8Naming
def purgeResources(settings):
    return (settings.get('resources-purge') or '').lower() in YES


# noinspection PyPep8Naming
def overwriteResources(settings):
    return (settings.get('resources-overwrite') or '').lower() in YES


# noinspection PyPep8Naming
def populateTarball(tar, directory, prefix=''):
    for name in directory.listDirectory():
        if directory.isDirectory(name):
            # Create sub-directory
            info = tarfile.TarInfo(prefix + name)
            info.type = tarfile.DIRTYPE
            tar.addfile(info, BytesIO())

            # Populate sub-directory
            populateTarball(tar, directory[name], prefix + name + '/')
        else:
            data = directory.readFile(name)

            # Fix dotted names filtered by resource directory API
            if name.endswith('.dotfile'):
                name = '.' + name[:-8]

            info = tarfile.TarInfo(prefix + name)
            info.size = len(data)
            tar.addfile(info, BytesIO(data))


# noinspection PyPep8Naming
def createTarball(directory):
    fb = BytesIO()
    tar = tarfile.open(fileobj=fb, mode='w:gz')

    # Recursively populate tarball
    populateTarball(tar, directory)

    tar.close()
    return fb.getvalue()


@cache('permissions')
def getPermissions(settings):
    if 'permissions' in settings:

        def split(s):
            parts = s.split(' ', 1)
            return parts[0].strip(), parts[1].strip()

        return dict([split(permission) for permission in
                     filter(bool, settings['permissions'].split('\n'))
                     if not permission.strip().startswith('#')])
    else:
        return {}


def getMessageCatalogs(locales):
    catalogs = {}

    # Parse message catalogs from the theme
    for language in locales.listDirectory():
        if not locales.isDirectory(language):
            continue
        directory = locales[language]
        if not directory.isDirectory('LC_MESSAGES'):
            continue
        directory = directory['LC_MESSAGES']
        for po in directory.listDirectory():
            if not po.endswith('.po') or not directory.isFile(po):
                continue
            domain = po.rsplit('.', 1)[0]
            catalogs.setdefault(domain, {})
            catalogs[domain][language] = MessageCatalog(language, domain)
            for msg in pofile(str(directory.readFile(po))):
                if not msg.msgstr:
                    continue  # Disallows overrides with empty strings
                catalogs[domain][language].setMessage(
                    msg.msgid, unicode(msg.msgstr, 'utf-8', 'ignore'))

    return catalogs


def copyResources(source, destination, purge=False, overwrite=False, depth=0):
    for name in source.listDirectory():
        if purge and name in destination and depth > 0:
            del destination[name]
        if source.isDirectory(name):
            destination.makeDirectory(name)
            copyResources(source[name], destination[name],
                          purge, overwrite, depth + 1)
        elif overwrite or name not in destination:
            if destination.isDirectory(name):
                del destination[name]
            fp = source.openFile(name)
            destination.writeFile(name, fp)
            fp.close()


class CatalogMessages(object):
    def __init__(self, catalog):
        self._catalog = dict([(msg['msgid'], msg['msgstr']) for msg in
                              catalog.getMessages()])


_data = property(lambda self: self)
_catalog = property(lambda self: CatalogMessages(self))
