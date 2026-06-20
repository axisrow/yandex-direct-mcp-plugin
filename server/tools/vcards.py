"""MCP tools for vCard management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors
from server.tools.helpers import (
    CliOption,
    append_cli_options,
    append_pagination,
    check_batch_limit,
    run_single_id_batch,
    tool_error_dict,
)

VCARD_0312_OPTIONS = (
    CliOption("instant_messenger_client", "--instant-messenger-client"),
    CliOption("instant_messenger_login", "--instant-messenger-login"),
    CliOption("point_on_map_x", "--point-on-map-x"),
    CliOption("point_on_map_y", "--point-on-map-y"),
    CliOption("point_on_map_x1", "--point-on-map-x1"),
    CliOption("point_on_map_y1", "--point-on-map-y1"),
    CliOption("point_on_map_x2", "--point-on-map-x2"),
    CliOption("point_on_map_y2", "--point-on-map-y2"),
)


@mcp.tool(
    name="vcards_get",
    description="List vCards (business contact cards with address/phone shown with ads), optionally filtered by IDs (max 10). Use vcards_add to create, vcards_delete to remove. Call tool_help('vcards_get') for parameters.",
)
@handle_cli_errors
def vcards_list(
    ids: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
) -> list[dict] | dict:
    """List vCards.

    Args:
        ids: Comma-separated vCard IDs (max 10).
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
    """
    cmd = ["vcards", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        batch_error = check_batch_limit(normalized_ids)
        if batch_error:
            return tool_error_dict(batch_error)
        cmd.extend(["--ids", normalized_ids])
    append_pagination(cmd, limit, fetch_all, fields)
    return get_runner().run_json(cmd)


@mcp.tool(
    description="Add a vCard (business contact card with company name, address, and phone) to a campaign. Use vcards_get to list existing vCards. Call tool_help('vcards_add') for parameters.",
)
@handle_cli_errors
def vcards_add(
    campaign_id: int,
    country: str,
    city: str,
    company_name: str,
    work_time: str,
    phone_country_code: str,
    phone_city_code: str,
    phone_number: str,
    phone_extension: str | None = None,
    street: str | None = None,
    house: str | None = None,
    building: str | None = None,
    apartment: str | None = None,
    contact_person: str | None = None,
    contact_email: str | None = None,
    extra_message: str | None = None,
    ogrn: str | None = None,
    metro_station_id: int | None = None,
    instant_messenger_client: str | None = None,
    instant_messenger_login: str | None = None,
    point_on_map_x: str | None = None,
    point_on_map_y: str | None = None,
    point_on_map_x1: str | None = None,
    point_on_map_y1: str | None = None,
    point_on_map_x2: str | None = None,
    point_on_map_y2: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Add a vCard.

    CLI 0.3.8 dropped --json. Mirrors WSDL VCardAddItem exactly.

    Args:
        campaign_id: Campaign ID.
        country: Country.
        city: City.
        company_name: Company name.
        work_time: Work time string.
        phone_country_code: Phone country code.
        phone_city_code: Phone city code.
        phone_number: Phone number.
        phone_extension: Phone extension.
        street: Street.
        house: House.
        building: Building.
        apartment: Apartment.
        contact_person: Contact person.
        contact_email: Contact email.
        extra_message: Extra message.
        ogrn: OGRN.
        metro_station_id: Metro station ID.
        instant_messenger_client: Instant messenger client name.
        instant_messenger_login: Instant messenger login.
        point_on_map_x/point_on_map_y: Point-on-map coordinates.
        point_on_map_x1/point_on_map_y1: First map bounds coordinate pair.
        point_on_map_x2/point_on_map_y2: Second map bounds coordinate pair.
        dry_run: Show the direct request without sending it.
    """
    args = [
        "vcards",
        "add",
        "--campaign-id",
        str(campaign_id),
        "--country",
        country,
        "--city",
        city,
        "--company-name",
        company_name,
        "--work-time",
        work_time,
        "--phone-country-code",
        phone_country_code,
        "--phone-city-code",
        phone_city_code,
        "--phone-number",
        phone_number,
    ]
    if phone_extension is not None:
        args.extend(["--phone-extension", phone_extension])
    if street is not None:
        args.extend(["--street", street])
    if house is not None:
        args.extend(["--house", house])
    if building is not None:
        args.extend(["--building", building])
    if apartment is not None:
        args.extend(["--apartment", apartment])
    if contact_person is not None:
        args.extend(["--contact-person", contact_person])
    if contact_email is not None:
        args.extend(["--contact-email", contact_email])
    if extra_message is not None:
        args.extend(["--extra-message", extra_message])
    if ogrn is not None:
        args.extend(["--ogrn", ogrn])
    if metro_station_id is not None:
        args.extend(["--metro-station-id", str(metro_station_id)])
    append_cli_options(args, locals(), VCARD_0312_OPTIONS)
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)


@mcp.tool(
    description="Delete vCards by ID (max 10 per call). Use vcards_get to find IDs. Call tool_help('vcards_delete') for parameters.",
)
@handle_cli_errors
def vcards_delete(ids: str, dry_run: bool = False) -> dict:
    """Delete vCards.

    Args:
        ids: Comma-separated vCard IDs (max 10).
    """
    return run_single_id_batch(get_runner(), "vcards", "delete", ids, dry_run=dry_run)
