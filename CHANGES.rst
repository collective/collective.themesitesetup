Changelog
=========

1.5.1 (2017-06-15)
------------------

- Fix issue where it was not possible to install message catalogs with dot in domain
  [datakurre]


1.5.0 (2017-05-27)
------------------

- Pin zope.app.i18n < 4.0.0
  [datakurre]


1.4.1 (2017-04-11)
------------------

- Removed debug print
  [datakurre]


1.4.0 (2017-04-11)
------------------

- Patch TTW message catalogs to support plonejs18n view (translate-pattern),
  but note that with plonejsi18n TTW catalog overrides don't cascade with
  the existing catalogs
  [datakurre]

- Use theme cache for TTW permissions, because TTW permissions require that
  their existence is checked on each request
  [datakurre]


1.3.2 (2017-01-03)
------------------

- Fix issue where message catalog support allowed (mostly accidentally)
  overriding messages with empty strings. Messages with empty strings are
  now ignored.
  [datakurre]


1.3.1 (2016-12-14)
------------------

- Add to purge plone.app.blocks' site layout cache after resource directory
  copy
  [datakurre]


1.3.0 (2016-11-22)
------------------

- Add support for populating persistent (plone.resource) resource directories
  [datakurre]

- Refactor permission support to use zope.app.localpermission
  [datakurre]


1.2.0 (2016-08-17)
------------------

- Add support for TTW custom permissions
  [datakurre]


1.1.0 (2016-08-12)
------------------

- Add support for populating Dexterity content type models from theme
  from ``./models/Xxxxxx.xml``
  [datakurre]


1.0.1 (2016-08-11)
------------------

- Fix issue where translationdomain internals prevented updating existing
  catalog
  [datakurre]


1.0.0 (2016-08-11)
------------------

- Add support for registering i18n message catalogs directly from theme
  from ``./locales/xx/LC_MESSAGES/yyyyy.po``
  [datakurre]


0.13.0 (2015-04-23)
-------------------

- Add support for exporting and importing plone.app.contenttypes -content
  [datakurre]


0.12.0 (2015-04-04)
-------------------

- Move custom GS import export adapters to external configuration
  [datakurre]

- Fix to register setup forms for p.a.theming layer
  [datakurre]


0.11.1 (2015-04-04)
-------------------

- Update README
  [datakurre]


0.11.0 (2015-04-04)
-------------------

- Add site setup import view to allow testing or manual upgrading of site
  setups
  [datakurre]

- Add option to disable setup steps import via plugin configuration variable in
  theme manifest (either with ``enabled = false`` or ``disabled = true``)
  [datakurre]


0.10.0 (2015-04-03)
-------------------

- Add GS content export support to include non-CMF-containers
  marked with
  ``collective.themesitesetup.interfaces.IGenericSetupExportableContainer``
  [datakurre]

- Add GS content export/import to support non-CMF-containers, PythonScripts
  and PageTemplates.
  [datakurre]


0.9.0 (2015-04-01)
------------------

- First release.
