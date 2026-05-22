Issue #43 CLI Parity
====================

This page captures the current CLI parity scope for issue ``#43``.

In-scope groups
---------------

.. list-table::
   :header-rows: 1

   * - CLI group
     - CLI command
     - MCP tool
     - Status
     - Notes
   * - ``ads``
     - ``get``
     - ``ads_get``
     - implemented
     - Campaign-scoped list wrapper with existing batch/foreign-account guards.
   * - ``ads``
     - ``add``
     - ``ads_add``
     - implemented
     - CLI-backed wrapper.
   * - ``ads``
     - ``update``
     - ``ads_update``
     - implemented
     - Supports typed update fields; status changes use suspend/resume/archive/unarchive tools.
   * - ``ads``
     - ``delete`` / ``moderate`` / ``suspend`` / ``resume`` / ``archive`` / ``unarchive``
     - ``ads_delete`` / ``ads_moderate`` / ``ads_suspend`` / ``ads_resume`` / ``ads_archive`` / ``ads_unarchive``
     - implemented
     - Batch-limited wrappers.
   * - ``campaigns``
     - ``get``
     - ``campaigns_get``
     - implemented
     - State filtering remains MCP-side.
   * - ``campaigns``
     - ``update``
     - ``campaigns_update``
     - implemented
     - Supports typed ``name``, ``status``, ``budget``, ``start_date``, and ``end_date`` updates; empty updates are rejected.
   * - ``campaigns``
     - ``add`` / ``delete`` / ``archive`` / ``unarchive`` / ``suspend`` / ``resume``
     - matching MCP tools
     - implemented
     - CLI-backed wrappers.
   * - ``keywords``
     - ``get``
     - ``keywords_get``
     - implemented
     - Campaign-scoped list wrapper.
   * - ``keywords``
     - ``update``
     - ``keywords_update``
     - implemented
     - Supports typed ``keyword`` and user-param updates; bid changes use ``keywordbids_set``.
   * - ``keywords``
     - ``add`` / ``delete`` / ``suspend`` / ``resume``
     - matching MCP tools
     - implemented
     - CLI-backed wrappers. ``archive`` / ``unarchive`` are not exposed because direct-cli has no such subcommands.
   * - ``reports``
     - ``get``
     - ``reports_get``
     - implemented
     - Opinionated campaign-performance wrapper retained for MCP convenience.
   * - ``reports``
     - ``list-types``
     - ``reports_list_types``
     - implemented
     - Exposes report type discovery directly.

Deferred backlog outside issue #43
----------------------------------

The following Phase 2 groups are intentionally tracked outside the acceptance scope of issue ``#43``:

- ``adgroups``
- ``bids``
- ``bidmodifiers``
- ``audiencetargets``
- ``sitelinks``
- ``vcards``
- ``adimages``
- ``adextensions``
- ``dictionaries``
- ``changes``
- ``clients``
- ``agencyclients``
- ``feeds``
- ``retargeting``
- ``dynamictargets``
- ``creatives``
- ``keywordsresearch``
- ``leads``
- ``negativekeywords``
- ``smarttargets``
- ``turbopages``
