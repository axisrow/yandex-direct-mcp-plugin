"""MCP tools for vCard management."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit, run_single_id_batch


@mcp.tool(name="vcards_get")
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
            return batch_error.__dict__
        cmd.extend(["--ids", normalized_ids])
    if limit is not None:
        cmd.extend(["--limit", str(limit)])
    if fetch_all:
        cmd.append("--fetch-all")
    if fields is not None:
        cmd.extend(["--fields", fields])
    return get_runner().run_json(cmd)


@mcp.tool()
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
    if dry_run:
        args.append("--dry-run")
    return get_runner().run_json(args)


@mcp.tool()
@handle_cli_errors
def vcards_delete(ids: str, dry_run: bool = False) -> dict:
    """Delete vCards.

    Args:
        ids: Comma-separated vCard IDs (max 10).
    """
    return run_single_id_batch(get_runner(), "vcards", "delete", ids, dry_run=dry_run)
