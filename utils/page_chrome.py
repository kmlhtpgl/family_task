"""Shared text-first header for the classic workspace routes."""

import streamlit as st
from html import escape


def render_page_header(title: str, description: str, eyebrow: str = "Family workspace") -> None:
    st.markdown(
        f'<div class="page-heading">'
        f'<div class="page-heading__eyebrow">{eyebrow}</div>'
        f'<div class="page-heading__title">{title}</div>'
        f'<div class="page-heading__description">{description}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_stat_strip(items: list[tuple[str, str, str]]) -> None:
    """Render the dense stat row shared by profile and planning pages."""
    cards = "".join(
        f'<div class="route-stat"><div class="route-stat__value">{escape(str(value))}</div>'
        f'<div class="route-stat__label">{escape(label)}</div>'
        f'<div class="route-stat__hint">{escape(hint)}</div></div>'
        for label, value, hint in items
    )
    st.markdown(f'<div class="route-stat-strip">{cards}</div>', unsafe_allow_html=True)


def render_profile_identity(name: str, role: str, detail: str, rank: str) -> None:
    st.markdown(
        f'<div class="profile-identity">'
        f'<div><div class="profile-identity__role">{escape(role)}</div>'
        f'<div class="profile-identity__name">{escape(name)}</div>'
        f'<div class="profile-identity__detail">{escape(detail)}</div></div>'
        f'<div class="profile-identity__rank">{escape(rank)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
