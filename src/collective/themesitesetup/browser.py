# -*- coding: utf-8 -*-
from collective.themesitesetup.interfaces import DEFAULT_ENABLED_PROFILE_NAME
from collective.themesitesetup.utils import createTarball
from io import BytesIO
from plone import api
from plone.autoform import directives
from plone.autoform.form import AutoExtensibleForm
from plone.supermodel import model
from plone.z3cform.layout import FormWrapper
from z3c.form import button
from z3c.form import form
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope import schema
from zope.globalrequest import getRequest
from zope.interface import provider
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
import Acquisition
import re
import tarfile
from six.moves import filter
from six.moves import map


# noinspection PyUnusedLocal,PyPep8Naming
@provider(IContextSourceBinder)
def genericSetupExportStepsSource(context):
    portal_setup = api.portal.get_tool('portal_setup')
    export_steps = portal_setup.listExportSteps()
    return SimpleVocabulary(list(map(SimpleTerm, list(map(str, export_steps)))))


# noinspection PyUnusedLocal,PyPep8Naming
@provider(IContextSourceBinder)
def genericSetupImportStepsSource(context):
    portal_setup = api.portal.get_tool('portal_setup')
    export_steps = portal_setup.listImportSteps()
    return SimpleVocabulary(list(map(SimpleTerm, list(map(str, export_steps)))))


# noinspection PyUnusedLocal,PyPep8Naming
@provider(IContextSourceBinder)
def resourceDirectorySubDirectoriesSource(context):
    # Our context is portal root, because z3c.form would not work otherwise
    try:
        context = getRequest()['PUBLISHED'].form_instance.directory
    except AttributeError:
        # For InlineValidationView
        context = getRequest()['PUBLISHED'].context.form_instance.directory
    files = context.listDirectory()
    directories = [path for path in files
                   if context.isDirectory(path)]
    return SimpleVocabulary(list(map(SimpleTerm, list(map(str, directories)))))


class IExportForm(model.Schema):

    directory = schema.NativeStringLine(
        title=u'Directory name',
        description=u'Give name for the theme sub-directory, where '
                    u'the generated export should be saved to. '
                    u'If the directory already exists, '
                    u'its content may get overridden.',
        default=DEFAULT_ENABLED_PROFILE_NAME
    )

    directives.widget(steps=CheckBoxFieldWidget)
    steps = schema.List(
        title=u'Exported steps',
        description=u'Select the steps, which should be included in '
                    u'the export.',
        value_type=schema.Choice(
            title=u'Step name',
            source=genericSetupExportStepsSource
        ),
        default=['content']
    )


# noinspection PyPep8Naming
class ExportForm(AutoExtensibleForm, form.Form):
    schema = IExportForm
    ignoreContext = True

    label = u'Export site setup into theme'
    description = (u'Export the current site setup '
                   u'and save as editable files into this '
                   u'theme (or resource) directory.')

    def __init__(self, context, request, directory=None):
        self.directory = directory
        super(ExportForm, self).__init__(context, request)

    # noinspection PyUnusedLocal
    @button.buttonAndHandler(u'Export')
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        directoryName = (data.get('directory') or '').strip()
        exportSteps = list(filter(bool, list(map(str.strip, data.get('steps') or []))))

        if not directoryName or not exportSteps:
            return

        # Create export
        portal_setup = api.portal.get_tool('portal_setup')
        # noinspection PyProtectedMember
        tarball = portal_setup._doRunExportSteps(exportSteps)['tarball']

        # Open the exported tarball
        fb = BytesIO(tarball)
        tar = tarfile.open(fileobj=fb, mode='r:gz')

        # Create base directory
        if not self.directory.isDirectory(directoryName):
            self.directory.makeDirectory(directoryName)
        baseDirectory = self.directory[directoryName]

        # Export tarball contents into the base directory
        for info in tar:
            if info.type == tarfile.DIRTYPE:
                baseDirectory.makeDirectory(info.name)
            else:
                path = info.path

                # Fix dotted names filted by source dictory API
                path = re.sub('/\.([^/]+)', '/\\1.dotfile', path)

                baseDirectory.writeFile(path, tar.extractfile(info))

        # Close the tarfile
        tar.close()

        # Report success
        self.status = u'Done.'


class ExportFormView(FormWrapper):
    form = ExportForm

    def __init__(self, context, request):
        # z3c.forms cannot be rendered with resource directory as context
        super(ExportFormView, self).__init__(api.portal.get(), request)

        # noinspection PyUnresolvedReferences
        self.form_instance = self.form(Acquisition.aq_inner(self.context),
                                       self.request, context)
        self.form_instance.__name__ = self.__name__

        # Disable green border
        self.request.set('disable_border', True)


class IImportForm(model.Schema):

    directory = schema.Choice(
        title=u'Directory name',
        description=u'Give name for the theme sub-directory, where '
                    u'the imported steps should be read from.',
        source=resourceDirectorySubDirectoriesSource,
    )

    directives.widget(steps=CheckBoxFieldWidget)
    steps = schema.List(
        title=u'Imported steps',
        description=u'Select the steps, which should be included in '
                    u'the import.',
        value_type=schema.Choice(
            title=u'Step name',
            source=genericSetupExportStepsSource
        ),
        default=['content']
    )


# noinspection PyPep8Naming
class ImportForm(AutoExtensibleForm, form.Form):
    schema = IImportForm
    ignoreContext = True

    label = u'Import site setup from theme'
    description = (u'Import the selected site setup '
                   u'from theme (or resource) directory.')

    def __init__(self, context, request, directory=None):
        self.directory = directory
        super(ImportForm, self).__init__(context, request)

    # noinspection PyUnusedLocal
    @button.buttonAndHandler(u'Import')
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        directoryName = (data.get('directory') or '').strip()
        importSteps = list(filter(bool, list(map(str.strip, data.get('steps') or []))))

        if not directoryName or not importSteps:
            return

        allImportSteps = genericSetupImportStepsSource(self.context)
        blacklistedSteps = [step.value for step in allImportSteps
                            if step.value not in importSteps]
        tarball = createTarball(self.directory[directoryName])

        # Create import
        portal_setup = api.portal.get_tool('portal_setup')
        portal_setup.runAllImportStepsFromProfile(
            None, purge_old=False, archive=tarball,
            blacklisted_steps=blacklistedSteps
        )

        # Report success
        self.status = u'Done.'


class ImportFormView(FormWrapper):
    form = ImportForm

    def __init__(self, context, request):
        # z3c.forms cannot be rendered with resource directory as context
        super(ImportFormView, self).__init__(api.portal.get(), request)

        # noinspection PyUnresolvedReferences
        self.form_instance = self.form(Acquisition.aq_inner(self.context),
                                       self.request, context)
        self.form_instance.__name__ = self.__name__

        # Disable green border
        self.request.set('disable_border', True)
