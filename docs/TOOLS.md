# MCP Tools

## MCP Tools (146 total) + 1 Prompt

The canonical source of truth for tool names is `server/contract.py`.
Naming follows `service_method` from `tapi-yandex-direct`/`direct-cli`;
WSDL/reports spec wins when there is drift.

### Direct API tools (139)

| Tool | Purpose |
|---|---|
| `campaigns_get` | List campaigns, optional state/status/type filter |
| `campaigns_update` | Update campaign fields |
| `campaigns_add` | Create campaign |
| `campaigns_delete` | Delete campaigns |
| `campaigns_archive` | Archive campaigns |
| `campaigns_unarchive` | Unarchive campaigns |
| `campaigns_suspend` | Suspend campaigns |
| `campaigns_resume` | Resume campaigns |
| `adgroups_get` | List ad groups |
| `adgroups_add` | Create ad group (single, or batch via `from_file`/`adgroups_json`) |
| `adgroups_update` | Update ad group (single by id, or batch via `from_file`/`adgroups_json`) |
| `adgroups_delete` | Delete ad groups |
| `ads_get` | List ads by campaign IDs |
| `ads_add` | Create ad (single, or batch via `from_file`/`ads_json`) |
| `ads_update` | Update ad (single by id, or batch via `from_file`/`ads_json`); `clear_image_hash` resets AdImageHash |
| `ads_delete` | Delete ads |
| `ads_moderate` | Submit ads for moderation |
| `ads_suspend` | Suspend ads |
| `ads_resume` | Resume suspended ads |
| `ads_archive` | Archive ads |
| `ads_unarchive` | Unarchive ads |
| `advideos_get` | List ad videos |
| `advideos_add` | Add ad video (url or video_data) |
| `adimages_get` | List ad images |
| `adimages_add` | Add ad image |
| `adimages_delete` | Delete images |
| `adextensions_get` | List ad extensions |
| `adextensions_add` | Add extension |
| `adextensions_delete` | Delete extensions |
| `keywords_get` | List keywords by campaign IDs |
| `keywords_update` | Update keyword text or user params (use `keywordbids_set` for bids) |
| `keywords_add` | Add keywords |
| `keywords_delete` | Delete keywords |
| `keywords_suspend` | Suspend keywords |
| `keywords_resume` | Resume keywords |
| `keywordbids_get` | List keyword bids |
| `keywordbids_set` | Set keyword bids |
| `keywordbids_set_auto` | Set keyword bids to auto strategy |
| `bids_get` | List bids |
| `bids_set` | Set bid for campaign |
| `bids_set_auto` | Set bids to auto strategy |
| `bidmodifiers_get` | List bid modifiers |
| `bidmodifiers_add` | Add bid modifier |
| `bidmodifiers_set` | Update existing bid modifier by `id` (use `bidmodifiers_add` to create) |
| `bidmodifiers_delete` | Delete bid modifiers |
| `sitelinks_get` | List sitelinks sets |
| `sitelinks_add` | Add sitelinks set |
| `sitelinks_delete` | Delete sitelinks |
| `vcards_get` | List vCards |
| `vcards_add` | Add vCard |
| `vcards_delete` | Delete vCards |
| `audiencetargets_get` | List audience targets |
| `audiencetargets_add` | Add audience target |
| `audiencetargets_delete` | Delete targets |
| `audiencetargets_suspend` | Suspend targets |
| `audiencetargets_resume` | Resume targets |
| `audiencetargets_set_bids` | Set bids for audience targets |
| `retargeting_get` | List retargeting lists |
| `retargeting_add` | Add retargeting list |
| `retargeting_update` | Update retargeting list |
| `retargeting_delete` | Delete retargeting lists |
| `dynamicads_get` | List dynamic ad targets (webpages) |
| `dynamicads_add` | Add dynamic ad target |
| `dynamicads_delete` | Delete dynamic ad targets |
| `dynamicads_suspend` | Suspend dynamic ad targets |
| `dynamicads_resume` | Resume dynamic ad targets |
| `dynamicads_set_bids` | Set bids for dynamic ad targets |
| `dynamicfeedadtargets_get` | List dynamic feed ad targets |
| `dynamicfeedadtargets_add` | Add dynamic feed ad target |
| `dynamicfeedadtargets_delete` | Delete dynamic feed ad target |
| `dynamicfeedadtargets_suspend` | Suspend dynamic feed ad targets |
| `dynamicfeedadtargets_resume` | Resume dynamic feed ad targets |
| `dynamicfeedadtargets_set_bids` | Set bids for dynamic feed ad targets |
| `smartadtargets_get` | List smart ad targets |
| `smartadtargets_add` | Add smart ad target |
| `smartadtargets_update` | Update smart ad target |
| `smartadtargets_delete` | Delete smart ad targets |
| `smartadtargets_suspend` | Suspend smart ad targets |
| `smartadtargets_resume` | Resume smart ad targets |
| `smartadtargets_set_bids` | Set bids for smart ad targets |
| `strategies_get` | List bidding strategies |
| `strategies_add` | Add bidding strategy |
| `strategies_update` | Update bidding strategy |
| `strategies_archive` | Archive bidding strategy |
| `strategies_unarchive` | Unarchive bidding strategy |
| `negativekeywordsharedsets_get` | List negative keyword shared sets |
| `negativekeywordsharedsets_add` | Add negative keyword shared set |
| `negativekeywordsharedsets_update` | Update negative keyword shared set |
| `negativekeywordsharedsets_delete` | Delete negative keyword shared set |
| `agencyclients_get` | List agency clients |
| `agencyclients_add` | Add client to agency |
| `agencyclients_update` | Update agency client |
| `agencyclients_add_passport_organization` | Add agency client backed by Passport org |
| `agencyclients_add_passport_organization_member` | Invite user to Passport org client |
| `businesses_get` | List businesses |
| `dictionaries_get` | Get dictionary data |
| `dictionaries_get_geo_regions` | Get geo regions dictionary |
| `changes_check` | Check changes since timestamp (filter by exactly one of campaign_ids/ad_group_ids/ad_ids; limits 3000/10000/50000) |
| `changes_check_campaigns` | Check campaign changes |
| `changes_check_dictionaries` | Check dictionary changes |
| `clients_get` | Get client info |
| `clients_update` | Update client |
| `keywordsresearch_has_search_volume` | Check keyword search volume |
| `keywordsresearch_deduplicate` | Deduplicate keywords |
| `leads_get` | List leads |
| `feeds_get` | List feeds |
| `feeds_add` | Add feed |
| `feeds_update` | Update feed |
| `feeds_delete` | Delete feeds |
| `creatives_get` | List creatives |
| `creatives_add` | Add creative |
| `turbopages_get` | List turbo pages |
| `reports_get` | Campaign statistics for date range |
| `reports_custom` | Full Reports API surface: arbitrary FieldNames, filters, ordering, pagination, file output, processing-mode/language/attribution/skip-* CLI 0.3.10 flags; honors `response_format` (json/tsv/csv/table) both for in-memory and `output_path` |
| `v4account_get_accounts` | Read v4 Live shared accounts via AccountManagement Get (pass `logins` OR `account_ids`). |
| `v4account_update_account` | Update v4 Live shared-account settings via AccountManagement Update (dry_run or sandbox required). |
| `v4account_deposit` | Deposit funds via AccountManagement Deposit. Finance/master tokens MUST come from env (`YANDEX_DIRECT_FINANCE_TOKEN`, `YANDEX_DIRECT_MASTER_TOKEN`). |
| `v4account_invoice` | Issue invoice payments via AccountManagement Invoice. Same env-only token policy as deposit. |
| `v4account_transfer_money` | Transfer funds between shared accounts via AccountManagement TransferMoney. Same env-only token policy. |
| `v4account_enable_shared_account` | Enable v4 Live shared account in dry-run or sandbox |
| `balance_get` | Read account money balance (v4 Live AccountManagement, read-only) |
| `v4events_get_events_log` | Get v4 Live events log entries |
| `v4forecast_create` | Create v4 Live budget forecast |
| `v4forecast_list` | List v4 Live budget forecasts |
| `v4forecast_get` | Get a ready v4 Live budget forecast |
| `v4forecast_delete` | Delete a v4 Live budget forecast |
| `v4wordstat_create_report` | Create v4 Live Wordstat report |
| `v4wordstat_list_reports` | List v4 Live Wordstat reports |
| `v4wordstat_get_report` | Get a ready v4 Live Wordstat report |
| `v4wordstat_delete_report` | Delete v4 Live Wordstat report |
| `v4goals_get_stat_goals` | Get Metrica stat goals available for campaigns (v4 Live) |
| `v4goals_get_retargeting_goals` | Get retargeting goals for campaigns (v4 Live) |
| `v4keywords_get_suggestion` | Get related keyword suggestions (up to 20 phrases; spends API points) |
| `v4adimage_get` | Read ad-image associations (AdImageAssociation Get) |
| `v4adimage_set` | Link/unlink ad images (AdImageAssociation Set) |
| `v4tags_get_campaigns` | Get campaign tags (v4 Live GetCampaignsTags) |
| `v4tags_get_banners` | Get banner tag IDs (v4 Live GetBannersTags) |
| `v4tags_update_campaigns` | Replace campaign tags (v4 Live UpdateCampaignsTags) |
| `v4tags_update_banners` | Replace banner tag assignments (v4 Live UpdateBannersTags) |

### CLI helper tools (3)

These are public but explicitly not 1:1 Direct API methods.

| Tool | Purpose |
|---|---|
| `agencyclients_delete` | Remove client from agency (no API backing) |
| `dictionaries_list_names` | List available dictionary names |
| `reports_list_types` | List available report types |

### Plugin tools (4)

Auth/utility tools unrelated to Direct API parity.

| Tool | Purpose |
|---|---|
| `auth_status` | Check direct auth profile status |
| `auth_setup` | Submit authorization code or direct token |
| `auth_login` | Interactive OAuth flow with elicitation |
| `tool_help` | Return the full docstring (parameters, examples, constraints) for any tool on demand. Every tool exposes only a one-line description to keep startup context small; call `tool_help('<name>')` before using an unfamiliar tool. Omit the name to list all tools. |

| Prompt | Purpose |
|---|---|
| `oauth_login` | Start direct auth profile authorization flow |
