"""Shared text-first header for the classic workspace routes."""

import streamlit as st


def render_page_header(title: str, description: str, eyebrow: str = "Family workspace") -> None:
    st.markdown(
        f'<div class="page-heading">'
        f'<div class="page-heading__eyebrow">{eyebrow}</div>'
        f'<div class="page-heading__title">{title}</div>'
        f'<div class="page-heading__description">{description}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
