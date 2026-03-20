from typing import Optional
from xml.etree.ElementTree import Element, SubElement, indent, tostring

from .models import PerscomPersonnel, SquadData, SquadMember

# The canonical Arma 3 squad DTD, served at /squad.dtd
SQUAD_DTD = """\
<?xml version="1.0"?>
<!ELEMENT squad (name, email, web?, picture?, title?, member+)>
<!ATTLIST squad nick CDATA #REQUIRED>
<!ELEMENT name (#PCDATA)>
<!ELEMENT email (#PCDATA)>
<!ELEMENT web (#PCDATA)>
<!ELEMENT picture (#PCDATA)>
<!ELEMENT title (#PCDATA)>
<!ELEMENT member (name, email?, icq?, remark?)>
<!ATTLIST member id CDATA #REQUIRED>
<!ATTLIST member nick CDATA #REQUIRED>
<!ELEMENT icq (#PCDATA)>
<!ELEMENT remark (#PCDATA)>
"""


def _build_nick(person: PerscomPersonnel) -> str:
    """
    Compose the nick attribute shown in-game.
    Format: "RANK Name"  e.g. "SGT V. Handberg"
    Falls back to just the name if no rank abbreviation is available.
    """
    if person.rank and person.rank.abbreviation:
        return f"{person.rank.abbreviation} {person.name}"
    return person.name


def _build_remark(person: PerscomPersonnel) -> str:
    """
    Compose the <remark> text — position name only (rank is already in nick).
    Example: "Squad Leader"
    """
    if person.position and person.position.name:
        return person.position.name
    return ""


def personnel_to_member(person: PerscomPersonnel) -> SquadMember:
    return SquadMember(
        steam_id=person.steamId64 or "",  # already filtered upstream
        nick=_build_nick(person),
        name=person.name,
        email=person.email or "",
        remark=_build_remark(person),
    )


def generate_squad_xml(data: SquadData) -> str:
    """
    Build the squad.xml string from a SquadData snapshot.
    Returns a complete XML document including the DOCTYPE declaration.
    """
    squad_el = Element("squad", nick=data.tag)

    name_el = SubElement(squad_el, "name")
    name_el.text = data.name

    email_el = SubElement(squad_el, "email")
    email_el.text = data.email

    if data.web:
        web_el = SubElement(squad_el, "web")
        web_el.text = data.web

    if data.logo:
        pic_el = SubElement(squad_el, "picture")
        pic_el.text = data.logo

    if data.title:
        title_el = SubElement(squad_el, "title")
        title_el.text = data.title

    for member in data.members:
        mem_el = SubElement(squad_el, "member", id=member.steam_id, nick=member.nick)

        m_name = SubElement(mem_el, "name")
        m_name.text = member.name

        m_email = SubElement(mem_el, "email")
        m_email.text = member.email

        m_icq = SubElement(mem_el, "icq")
        m_icq.text = ""

        m_remark = SubElement(mem_el, "remark")
        m_remark.text = member.remark

    indent(squad_el, space="  ")
    body = tostring(squad_el, encoding="unicode", xml_declaration=False)

    return (
        '<?xml version="1.0"?>\n'
        '<!DOCTYPE squad SYSTEM "squad.dtd">\n'
        f"{body}\n"
    )
