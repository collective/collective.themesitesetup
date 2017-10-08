# -*- coding: utf-8 -*-
from AccessControl.Permission import addPermission
from Acquisition import aq_base
from collective.themesitesetup.interfaces import DEFAULT_DISABLED_PROFILE_NAME
from collective.themesitesetup.interfaces import DEFAULT_ENABLED_LOCALES_NAME
from collective.themesitesetup.interfaces import DEFAULT_ENABLED_MODELS_NAME
from collective.themesitesetup.interfaces import DEFAULT_ENABLED_PROFILE_NAME
from collective.themesitesetup.interfaces import DEFAULT_ENABLED_RESOURCES_NAME
from collective.themesitesetup.utils import createTarball
from collective.themesitesetup.utils import getMessageCatalogs
from collective.themesitesetup.utils import getPermissions
from collective.themesitesetup.utils import getSettings
from collective.themesitesetup.utils import isEnabled
from collective.themesitesetup.utils import overwriteModels
from collective.themesitesetup.utils import overwriteResources
from collective.themesitesetup.utils import purgeResources
from collective.themesitesetup.utils import copyResources
from plone.app.theming.interfaces import IThemePlugin
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.dexterity.fti import DexterityFTIModificationDescription
from plone import api
from plone.resource.interfaces import IResourceDirectory
from plone.resource.interfaces import IWritableResourceDirectory
from plone.resource.utils import queryResourceDirectory
from plone.supermodel import loadString
from plone.supermodel.parser import SupermodelParseError
from zope.app.i18n.translationdomain import TranslationDomain
from zope.app.localpermission import LocalPermission
from zope.component import getSiteManager
from zope.component import queryUtility
from zope.event import notify
from zope.i18n import ITranslationDomain
from zope.interface import implements
from zope.lifecycleevent import ObjectModifiedEvent
from zope.security.interfaces import IPermission
from zope.security.permission import Permission
import logging

logger = logging.getLogger('collective.themesitesetup')


# noinspection PyPep8Naming
class GenericSetupPlugin(object):
    """This plugin can be used to import generic setup profiles
    when theme is enabled or disabled.

    Relative directory paths for importable generic setup profiles can
    be defined in the theme manifest::

        [theme:genericsetup]
        install = profile
        uninstall =

    """

    implements(IThemePlugin)

    dependencies = ()

    def onDiscovery(self, theme, settings, dependenciesSettings):
        pass

    def onCreated(self, theme, settings, dependenciesSettings):
        pass

    def onEnabled(self, theme, settings, dependenciesSettings):  # noqa
        res = queryResourceDirectory(THEME_RESOURCE_NAME, theme)
        if res is None:
            return

        # We need to get settings by ourselves to avoid p.a.theming caching
        settings = getSettings(res)
        if not isEnabled(settings):
            return

        # Remove imported folders not-required on run-time
        autocleanup = (settings.get('self-destruct') or '').lower() in (
            'true', 'yes', 'on', '1'
        )

        # Register permissions
        sm = getSiteManager()
        for key, value in getPermissions(settings).items():
            util = sm.queryUtility(IPermission, name=key)
            if util is None:
                name = str('collective.themesitesetup.permission.' + key)
                util = LocalPermission(value, u'')
                util.id = key
                util.__name__ = name
                util.__parent__ = aq_base(sm)
                sm._setObject(
                    name, util, set_owner=False, suppress_events=True)
                sm.registerUtility(
                    util, provided=IPermission, name=key)
                addPermission(str(value))

        # Import GS profile
        directoryName = DEFAULT_ENABLED_PROFILE_NAME
        if 'install' in settings:
            directoryName = settings['install']

        directory = None
        if res.isDirectory(directoryName):
            directory = res[directoryName]

        if directory:
            tarball = createTarball(directory)
            portal_setup = api.portal.get_tool('portal_setup')
            portal_setup.runAllImportStepsFromProfile(
                None, purge_old=False, archive=tarball)
            # Self-destruct imported profile
            if autocleanup and IWritableResourceDirectory.providedBy(res):
                del res[directoryName]

        # Register locales
        localesDirectoryName = DEFAULT_ENABLED_LOCALES_NAME
        if 'locales' in settings:
            localesDirectoryName = settings['locales']

        if res.isDirectory(localesDirectoryName):
            catalogs = getMessageCatalogs(res[localesDirectoryName])
            for domain in catalogs:
                util = sm.queryUtility(ITranslationDomain, name=domain)
                if not isinstance(util, TranslationDomain):
                    name = str('collective.themesitesetup.domain.' + domain)
                    util = TranslationDomain()
                    util.__name__ = name
                    util.__parent__ = aq_base(sm)
                    util.domain = domain
                    sm._setObject(
                        name, util, set_owner=False, suppress_events=True)
                    sm.registerUtility(
                        util, provided=ITranslationDomain, name=domain)
                for language in catalogs[domain]:
                    name = '.'.join(['collective.themesitesetup.catalog',
                                     res.__name__, domain, language])
                    if name in util:
                        try:
                            del util[name]
                        except ValueError:
                            pass
                    util[name] = catalogs[domain][language]
            # Self-destruct imported catalogs
            if autocleanup and IWritableResourceDirectory.providedBy(res):
                del res[localesDirectoryName]

        # Update Dexterity models
        modelsDirectoryName = DEFAULT_ENABLED_MODELS_NAME
        if 'models' in settings:
            modelsDirectoryName = settings['models']
        overwrite = overwriteModels(settings)

        if res.isDirectory(modelsDirectoryName):
            types_tool = api.portal.get_tool('portal_types')
            directory = res[modelsDirectoryName]
            for name in directory.listDirectory():
                if not name.endswith('.xml') or not directory.isFile(name):
                    continue
                fti = types_tool.get(name[:-4])
                if not fti:
                    continue
                model = unicode(directory.readFile(name), 'utf-8', 'ignore')
                if fti.model_source == model:
                    continue
                try:
                    loadString(model, fti.schema_policy)  # fail for errors
                except SupermodelParseError:
                    logger.error(
                        u'Error while parsing {0:s}/{1:s}/{2:s}'.format(
                            res.__name__, modelsDirectoryName, name))
                    raise
                # Set model source when model is empty of override is enabled
                desc = DexterityFTIModificationDescription('model_source',
                                                           fti.model_source)
                if not fti.model_source:
                    fti.model_source = model
                    notify(ObjectModifiedEvent(fti, desc))
                elif not loadString(fti.model_source, fti.schema_policy).schema.names():  # noqa
                    fti.model_source = model
                    notify(ObjectModifiedEvent(fti, desc))
                elif overwrite:
                    fti.model_source = model
                    notify(ObjectModifiedEvent(fti, desc))
            # Self-destruct imported models
            if autocleanup and IWritableResourceDirectory.providedBy(res):
                del res[modelsDirectoryName]

        # Copy resources
        resourcesDirectoryName = DEFAULT_ENABLED_RESOURCES_NAME
        if 'resources' in settings:
            resourcesDirectoryName = settings['resources']
        purge = purgeResources(settings)
        overwrite = overwriteResources(settings)
        root = queryUtility(IResourceDirectory, name=u'persistent')
        if root and res.isDirectory(resourcesDirectoryName):
            copyResources(res[resourcesDirectoryName], root, purge, overwrite)
            # Invalidate site layout cache of plone.app.blocks
            portal_catalog = api.portal.get_tool('portal_catalog')
            portal_catalog._increment_counter()
            # Self-desctruct imported resources
            if autocleanup and IWritableResourceDirectory.providedBy(res):
                del res[resourcesDirectoryName]

    def onDisabled(self, theme, settings, dependenciesSettings):  # noqa
        res = queryResourceDirectory(THEME_RESOURCE_NAME, theme)
        if res is None:
            return

        # We need to get settings by ourselves to avoid p.a.theming caching
        settings = getSettings(res)
        if not isEnabled(settings):
            return

        directoryName = DEFAULT_DISABLED_PROFILE_NAME
        if 'uninstall' in settings:
            directoryName = settings['uninstall']

        # Import GS (uninstall) profile
        directory = None
        if res.isDirectory(directoryName):
            directory = res[directoryName]

        if directory:
            tarball = createTarball(directory)
            portal_setup = api.portal.get_tool('portal_setup')
            portal_setup.runAllImportStepsFromProfile(
                None, purge_old=False, archive=tarball)

        # Unregister ALL themesitesetup based permissions
        sm = getSiteManager()
        permissions = getPermissions(settings)
        for key, util in list(sm.getUtilitiesFor(IPermission)):
            if isinstance(util, Permission) or isinstance(util, LocalPermission):  # noqa
                name = str('collective.themesitesetup.permission.' + key)
                if key not in permissions and name not in sm.objectIds():
                    continue  # Not a themesitesetup created permission
                if name in list(sm.objectIds()):
                    sm._delObject(name, suppress_events=True)
                # Note: The following lines may look weird, but exist because
                # we used to use transient Persistent class and these were the
                # lines, which properly unregistered those.
                util = sm._utility_registrations.get((IPermission, key))[0]
                sm.unregisterUtility(
                    util, provided=IPermission, name=key)
                sm.utilities.unsubscribe((), IPermission, util)

        # Unregister ALL themesitesetup based locales
        for domain, util in list(sm.getUtilitiesFor(ITranslationDomain)):
            util = sm.queryUtility(ITranslationDomain, name=domain)
            if isinstance(util, TranslationDomain):
                for name in list(util):
                    if not name.startswith('collective.themesitesetup.catalog.'):  # noqa
                        continue  # not a themesitesetup created domain
                    try:
                        del util[name]
                    except ValueError:
                        pass
                name = str('collective.themesitesetup.domain.' + domain)
                if name in list(sm.objectIds()):
                    sm._delObject(name, suppress_events=True)
                sm.unregisterUtility(
                    util, provided=ITranslationDomain, name=domain)

    def onRequest(self, request, theme, settings, dependenciesSettings):
        # Ensure that TTW permissions are registered also as Zope 2 permissions
        for permission in getPermissions(settings).values():
            addPermission(permission)
