collective.themesitesetup
=========================

.. image:: https://secure.travis-ci.org/datakurre/collective.themesitesetup.png
   :target: https://travis-ci.org/datakurre/collective.themesitesetup

**collective.themesitesetup** is a `plone.app.theming`_-plugin for
embedding GenericSetup_-steps into zipped theme packages.

**collective.themesitesetup** can automatically import one embedded set of
generic setup steps during theme activation and another one (so called
*uninstall profile*) when theme is deactivated. Yet, also additionals ets
can be embedded and imported manually.

See it activating theme site setup at: https://youtu.be/3vkrc7JFUU0

.. _plone.app.theming: https://pypi.python.org/pypi/plone.app.theming
.. _GenericSetup: https://pypi.python.org/pypi/Products.GenericSetup


Installation
------------

Simply include this package into your Plone site buildout by following
`the official instructions`_. This add-on doesn't require other activation,
but, of course, requires `plone.app.theming`_ to be activated.

.. _the official instructions: http://docs.plone.org/manage/installing/installing_addons.html


Configuration
-------------

This plugin is enabled for any theme by simply adding the following line into
theme's ``manifest.cfg``:

.. code:: ini

   [theme:genericsetup]

By default, this looks for the setup steps to be imported during activation
from theme's ``install``-subdirectory and the steps to be imported during
deactivation from theme's ``uninstall``-subdirectory. If such directory does
not exist, this plugin simply does not import any steps.

The default lookup directories can be customized by overriding the defaults
with custom values in theme's ``manifest.cfg``:

.. code:: ini

   [theme:genericsetup]
   install = my-install
   uninstall = my-uninstall

This plugin can also be disabled at any time simply by adding the line
``disabled = true`` into plugin's configuration in theme's ``manifest.cfg``:

.. code:: ini

   [theme:genericsetup]
   disabled = true


About security
--------------

The use of this package encourages storing importable Generic Setup profiles
(and later Dexterity XML models, localization catalogs and other resource
directories data) in theme. Because all the resources in theme are public with
know URLs, also all the data in theme meant to be imported by this package are
made public.

If you don't want to publish your Generic Setup profiles and other theme data
included only to be imported by this plugin, use the following option
``self-destruct = true`` to remove all the imported resources after theme
activation:

.. code:: ini

   [theme:genericsetup]
   self-destruct = true


Dexterity models
----------------

A usual use for this plugin is to ship a theme with pre-configured Dexterity
content types. Unfortunately, describing a Dexterity XML schema in type
description inline in type description XML is inconvenient (because the schema
must be escaped) and Dexterity only supports reading separate XML model
files from filesystem and filesystem Python packages. Fortunately, this
plugin allows populating existing Dexterity content types (and also the
ones installed with this plugin) with a matching model XML from the theme.

By default, the plugin loads model files from ``models``-subdirectory of the
them. Models must have matching filename with the content type id (with
``.xml`` extension). The default import directory can be changed with:

.. code:: ini

   [theme:genericsetup]
   models = my_models

The plugin does not overwrite existing models by default (unless they seem
empty), but this can be changed (e.g. for development purposes) with:

.. code:: ini

   [theme:genericsetup]
   models-overwrite = true


Message catalogs
----------------

This plugin can also be used to register (and unregister) i18n message
catalogs directly from the theme. By default, the plugin looks for message
catalogs from ``locales``-subdirectory of the theme, expecting the usual
message catalog directory structure:

.. code::

   ./locales/en/LC_MESSAGES/foo.po
   ./locales/en/LC_MESSAGES/bar.po

In the above example, two message catalogs, one for language ``en`` for domain
``foo`` and another for language ``en`` for domain ``bar`` are registered.

The default locales directory name can be changed with:

.. code:: ini

   [theme:genericsetup]
   locales = my_locales

The registered message catalogs are unregistered when the theme is deactivated.

.. note::

   The registered message catalogs use the persistent message catalog
   classes from *zope.app.i18n*. The existence of these catalogs can
   be confirmed from ZMI *Components*-tab from Plone site root by looking
   for *translationdomain* utilities with themesitesetup in their names.


Mosaic layouts (and other resources)
------------------------------------

This plugin can also be used to populate also other persistent resource
directories than theme directories. For example, with this plugin, your theme
could contain site and content layouts for Plone Mosaic. Layouts are copied
from theme into their own resource directory namespaces when theme is activated
(or updated). One layouts are copied, they are not removed, unless this plugin
is configured to purge those directories.

For example, theme containing single site layout and content layout, could
contain the following file structure:

.. code::

   ./resources/sitelayout/manifest.cfg
   ./resources/sitelayout/layout.html
   ./resources/contentlayout/manifest.cfg
   ./resources/contentlayout/layout.html

The default resources directory name can be from ``resources`` to e.g.
``designs`` with:

.. code:: ini

   [theme:genericsetup]
   resources = design

By default, this plugin never overwrites existing resources unless its
configuration option ``resources-overwrite`` is enabled:

.. code:: ini

   [theme:genericsetup]
   resources-overwrite = true

In addition, this plugin can be configured to purge existing directories
before copying with:

.. code:: ini

   [theme:genericsetup]
   resources-purge= true

Although, the plugin will still never remove top-level resources directories
(like ``theme``, ``sitelayout`` or ``contentlayout``).

.. note::

   Technically resources are simply copied into ``portal_resources`` and they
   can be manually removed via ZMI. Please, note that changes made in theme
   editor are not copied unless theme has been re-activated (or updated).


Permissions
-----------

This plugin has also experimental support for TTW custom permissions, which
are useful for more complex content management scenarios involving Dexterity
content types and workflows. New permissions are registered before the
GenericSetup profile get imported, to make to new permission to be available
during import.

Custom permissions are listed in theme's ``manifest.cfg`` in *id Title* format
as follow:

.. code:: ini

   [theme:genericsetup]
   permissions =
       mydomain.addMyProduct    MyDomain: Add My Product
       mydomain.removeMyProduct MyDomain: Remove My Product

Custom permissions are removed when theme is disabled. Yet, they disappear
from ZMI only when the site is restarted.

.. note::

   The registered persistent permissions use and depend on LocalPermission
   class from *zope.app.localpermission*. If this package is removed without
   uninstalling theme with permisions at first, *zope.app.localpermission*
   must exit to prevent possible errors caused by missing object class.

   In addition, permissions must be registered for Zope 2 in a non-persistent
   way, which requires restart to remove permissions from ZMI screens.
   Because of this, even installed permissions continue to work only as long
   as this package is available.

   The existence of these permissions can be confirmed from ZMI
   *Components*-tab from Plone site root by looking for *Permission* utilities,
   on ZMI security tab and e.g. in the options for Add permission in ZMI portal
   type factory information pages.


Exporting the site setup
------------------------

This plugin provides helper forms for exporting the current site setup
into a through-the-web created (writable) theme and importing that site setup
manually from the theme folder.

The export form is registered for the theme resource directory as
``@@export-site-setup`` and the import form as ``@@import-site-setup``.

The export form is useful for creating the initial site setup into the theme
directory. Simply

1. Create a new theme from Theming control panel

2. Go to the export form URL, e.g.
   ``http://localhost:8080/Plone/++theme++my-theme/@@export-site-setup``:

3. Choose the steps you wish to export and click *Export*.

.. image:: https://raw.githubusercontent.com/collective/collective.themesitesetup/master/docs/images/export-site-setup.png
   :width: 768px
   :align: center


Editing the site setup
----------------------

The site setup steps can be edited like any theme file through the
theme editor:

.. image:: https://raw.githubusercontent.com/collective/collective.themesitesetup/master/docs/images/edit-site-setup.png
   :width: 768px
   :align: center

**Tip:** You can Use `six feet up`_'s great `Generic Setup reference card`__ as
cheat cheet for editing the site setup files.

.. _six feet up: http://www.sixfeetup.com
__ http://www.sixfeetup.com/plone-cms/quick-reference-cards/generic_setup.pdf/view

**Note:** Because the theme editor hides all *dotfiles*, files starting with a
dot must be renamed to end with ``.dotfile`` (and to not start with a dot).


Importing the setup
-------------------

By default, this plugin is configured import setup steps from a directory
``install`` whenever the theme is activated, and steps from a directory
``uninstall``, when the theme is deactivated. Both, install and uninstall
step directory can be changed in the plugin configuration.

In addition, it's possible to import the embedded steps manually using
the import setup form. Simply

1. Go to the import form URL for your theme, e.g.
   ``http://localhost:8080/Plone/++theme++my-theme/@@import-site-setup``:

2. Choose the steps you wish to import and click *Import*.


Better site structure export and import
---------------------------------------

This package includes optional enhancements for the default Plone site
structure export and import.

The enhancements include:

- support for News Item contents
- support for Zope Page Templates
- support for Python Scripts
- support for exporting tagged hidden folders (like ``portal_skins/custom``)

The enhancements can be activated by including a special component
configuration file in your Plone buildout's instance parts with:

.. code:: ini

   [instance]
   ...
   zcml = collective.themesitesetup-extras

ZMI-only content, which is hidden in Plone (folders like ``portal_skins``) can
be included in the export by tagging the folders in ZMI interface tab with a
special marker interface::

    ``collective.themesitesetup.interfaces.IGenericSetupExportableContainer``


PageTemplates and PythonScripts can only be exported when they are located in a
ZMI-only container with this marker interface. So, if you'd like to export
contents in ``portal_skins/custom``, you should add one marker for
``portal_skins`` and the other for ``custom``.

This is only required when exporting ZMI-only content. Importing ZMI-only
content works according to normal structure import rules without these marker
interfaces.


About plone.app.contenttypes support
------------------------------------

`Better site structure export and import`_ described above must be enabled
to support exporting and importing site structures with
`plone.app.contenttypes`_ based content.

In addition, `plone.app.textfield`_ ``>=1.2.5`` is recommended to fix issue,
where structure import does not decode field value properly, causing
UnicodeDecodeErrors later.

.. _plone.app.contenttypes: https://pypi.python.org/pypi/plone.app.contenttypes
.. _plone.app.textfield: https://pypi.python.org/pypi/plone.app.textfield


About custom Dexterity content support
--------------------------------------

Importing site structures with custom Dexterity content types require custom
adapter to be implemented and registered for each content type

.. code:: python

   from Products.GenericSetup.interfaces import IContentFactory
   from collective.themesitesetup.content import DexterityContentFactoryBase
   from plone.dexterity.interfaces import IDexterityContent
   from zope.component import adapter
   from zope.interface import implementer

   @adapter(IDexterityContent)
   @implementer(IContentFactory)
   class MyTypeFactory(DexterityContentFactoryBase):
       portal_type = 'MyType'

.. code:: xml

   <adapter
       factory=".adapters.MyTypeFactory"
       name="MyType"
       />

This is not required when Dexterity content is only created into site root
or Archetypes based container.
