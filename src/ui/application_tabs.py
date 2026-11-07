"""Abas especializadas de visualização A4, edição de currículo e carta de apresentação."""
import streamlit as st
from typing import Callable
from src.core.resume_formatter import parse_resume_markdown, serialize_resume_markdown


def render_a4_preview_tab(formatted_html: str, file_stub: str):
    """Renderiza a aba de visualização da folha A4 e botão de download do HTML."""
    with st.container(horizontal=True, vertical_alignment="center"):
        st.caption("💡 **Dica de Impressão Limpa:** Clique em **'🖨️ Imprimir / Salvar como PDF'** no topo da folha abaixo. O respiro do topo da 2ª página sai 100% limpo e automático. Se o seu navegador exibir data/URL, desmarque **'Cabeçalhos e rodapés'** na janela de impressão.")
        st.space("stretch")
        st.download_button(
            label="Baixar HTML imprimível",
            data=formatted_html,
            file_name=f"Curriculo_{file_stub}.html",
            mime="text/html",
            icon=":material/download:"
        )
    st.components.v1.html(formatted_html, height=1050, scrolling=True)


def render_resume_editor_tab(
    filepath: str,
    resume_md: str,
    cover_letter_md: str,
    file_stub: str,
    save_edit_fn: Callable[[str, str, str], None],
):
    """Renderiza a aba de edição estruturada (layout travado) ou código Markdown completo do currículo."""
    st.markdown("#### :material/edit_note: Editor de Conteúdo do Currículo")
    st.caption("Ajuste os dados do currículo mantendo o layout rigorosamente travado ou edite o código Markdown completo. Ao salvar, a folha **Currículo (A4)** é recompilada instantaneamente.")

    edit_mode = st.radio(
        "Modo de Edição:",
        options=["Campos Estruturados (Layout Travado)", "Código Markdown Completo"],
        horizontal=True,
        key=f"edit_mode_{filepath}"
    )

    parsed_cv = parse_resume_markdown(resume_md)

    if edit_mode == "Campos Estruturados (Layout Travado)":
        st.info("💡 **Layout Travado:** Os campos abaixo preservam automaticamente os estilos, fontes e espaçamentos profissionais da folha A4 para garantir impressão impecável.")

        with st.container(border=True):
            st.markdown("##### :material/badge: Identificação & Cabeçalho")
            col_h1, col_h2 = st.columns([1, 1])
            with col_h1:
                field_name = st.text_input("Nome Completo", value=parsed_cv["name"], key=f"f_name_{filepath}")
            with col_h2:
                field_role = st.text_input("Cargo Alvo", value=parsed_cv["role"], key=f"f_role_{filepath}")
            field_contact = st.text_input(
                "Contatos & Links (Cidade, Email, Telefone, LinkedIn, GitHub)",
                value=parsed_cv["contact"],
                key=f"f_contact_{filepath}",
                help="Separe os itens por barras verticais ' | '"
            )

        st.markdown("##### :material/view_agenda: Seções do Currículo")
        updated_sections = []
        for idx, sec in enumerate(parsed_cv["sections"]):
            sec_title = sec.get("title", "")
            with st.expander(f":material/article: {sec_title}", expanded=True):
                new_sec_title = st.text_input(
                    "Título da Seção",
                    value=sec_title,
                    key=f"sec_title_{idx}_{filepath}"
                )
                is_skills = "SKILL" in sec_title.upper() or "HABILIDADE" in sec_title.upper()
                if is_skills:
                    st.caption("💡 Para a tabela de habilidades técnicas, mantenha a estrutura com barras: `| Categoria | Tecnologias |`")
                new_sec_content = st.text_area(
                    "Conteúdo da Seção",
                    value=sec.get("content", ""),
                    height=180 if not is_skills else 130,
                    key=f"sec_content_{idx}_{filepath}"
                )
                updated_sections.append({
                    "title": new_sec_title.strip(),
                    "content": new_sec_content.strip()
                })

        with st.container(horizontal=True, vertical_alignment="center"):
            btn_save_structured = st.button(
                "Salvar e Recompilar A4",
                type="primary",
                icon=":material/save:",
                key=f"btn_save_struct_{filepath}"
            )

        if btn_save_structured:
            new_data = {
                "name": field_name.strip(),
                "role": field_role.strip(),
                "contact": field_contact.strip(),
                "sections": updated_sections
            }
            final_compiled_md = serialize_resume_markdown(new_data)
            if not final_compiled_md.strip():
                st.error("O currículo não pode ficar vazio.", icon=":material/error:")
            else:
                save_edit_fn(final_compiled_md, cover_letter_md, "Currículo atualizado com layout travado! A folha A4 foi recompilada.")

    else:
        new_resume_md = st.text_area(
            "Conteúdo Markdown do Currículo",
            value=resume_md,
            height=480,
            key=f"editor_resume_md_{filepath}",
            help="Edite livremente em Markdown. Ao salvar, a folha A4 e os downloads serão atualizados."
        )

        with st.container(horizontal=True, vertical_alignment="center"):
            btn_save_md = st.button(
                "Salvar e Recompilar A4",
                type="primary",
                icon=":material/save:",
                key=f"btn_save_resume_md_{filepath}"
            )
            st.download_button(
                label="Baixar currículo (.md)",
                data=new_resume_md,
                file_name=f"Curriculo_{file_stub}.md",
                mime="text/markdown",
                icon=":material/download:",
                key=f"dl_md_{filepath}"
            )

        if btn_save_md:
            if not new_resume_md.strip():
                st.error("O currículo não pode ficar vazio.", icon=":material/error:")
            else:
                save_edit_fn(new_resume_md.strip(), cover_letter_md, "Currículo atualizado! A folha A4 foi recompilada com sucesso.")

        with st.expander(":material/visibility: Pré-visualizar Markdown renderizado na tela", expanded=False):
            st.markdown(new_resume_md if new_resume_md else "_Nenhum conteúdo de currículo encontrado._")


def render_cover_letter_tab(
    filepath: str,
    resume_md: str,
    cover_letter_md: str,
    has_cover_letter: bool,
    file_stub: str,
    save_edit_fn: Callable[[str, str, str], None],
):
    """Renderiza a aba de edição e download da carta de apresentação."""
    if cover_letter_md or has_cover_letter:
        st.markdown("#### :material/mail: Carta de Apresentação")
        st.caption("Personalize o texto da carta de apresentação gerada pela IA e salve as alterações.")

        new_cover_md = st.text_area(
            "Conteúdo da Carta de Apresentação (Markdown)",
            value=cover_letter_md,
            height=380,
            key=f"editor_cover_md_{filepath}"
        )

        with st.container(horizontal=True, vertical_alignment="center"):
            btn_save_letter = st.button(
                "Salvar Carta de Apresentação",
                type="primary",
                icon=":material/save:",
                key=f"btn_save_cover_{filepath}"
            )
            st.download_button(
                label="Baixar carta (.md)",
                data=new_cover_md,
                file_name=f"CoverLetter_{file_stub}.md",
                mime="text/markdown",
                icon=":material/download:",
                key=f"dl_letter_{filepath}"
            )

        if btn_save_letter:
            save_edit_fn(resume_md, new_cover_md.strip(), "Carta de apresentação atualizada com sucesso!")

        with st.expander(":material/visibility: Pré-visualizar carta renderizada", expanded=False):
            st.markdown(new_cover_md if new_cover_md else "_Nenhum conteúdo._")
    else:
        st.info("Esta aplicação não possui uma carta de apresentação gerada.")

