import streamlit as st
from src.core import profile_manager
from src.ui.navbar import clear_transient_state
from src.ui.components import page_header, login_gate, resume_input

def _initials(name: str, fallback: str) -> str:
    parts = (name or fallback or "?").split()
    return "".join(p[0] for p in parts[:2]).upper()

def render_profile_view():
    """
    Perfil do candidato: dados pessoais, currículo base e projetos do GitHub em cache.
    Esses dados preenchem o Otimizador automaticamente.
    """
    session = st.session_state.get("user_session", {})
    page_header("Meu perfil", "Salve uma vez e o Otimizador preenche tudo sozinho — menos digitação e menos tokens.")

    if session.get("is_guest", True):
        login_gate(
            "Perfil disponível após o login",
            "Crie sua conta para salvar seu currículo base, usuário do GitHub e projetos em cache.",
            key="profile"
        )
        return

    uid = session.get("user_id", "guest_local")
    email = session.get("email", "")
    prof = profile_manager.get_user_profile(uid, email)
    repos = prof.get("cached_repos", [])
    key_name, key_github, key_resume = f"profile_name_{uid}", f"profile_github_{uid}", f"profile_resume_{uid}"
    st.session_state.setdefault(key_name, prof.get("full_name", ""))
    st.session_state.setdefault(key_github, prof.get("github_username", ""))

    # Resumo no topo: preenchido no fim, quando os valores digitados já são conhecidos
    summary = st.container()

    col_main, col_side = st.columns([1.7, 1], gap="medium")

    with col_side:
        with st.container(border=True):
            st.markdown("#### :material/person: Dados pessoais")
            name = st.text_input("Nome completo", key=key_name, placeholder="Como aparece no currículo")
            github = st.text_input("Usuário do GitHub", key=key_github, placeholder="ex: octocat", icon=":material/alternate_email:")
            st.text_input("E-mail da conta", value=email, disabled=True, icon=":material/mail:")

        with st.container(border=True):
            st.markdown(f"#### :material/folder_code: Projetos do GitHub :gray-badge[{len(repos)}]")
            st.caption("Ficam em cache para não consultar o GitHub (nem gastar tokens) a cada otimização.")
            if st.button("Atualizar projetos do GitHub", icon=":material/sync:", width="stretch", key="btn_sync_gh_cache", disabled=not github.strip()):
                clear_transient_state()
                with st.spinner(f"Buscando projetos públicos de @{github}..."):
                    from src.agents.nodes import github_researcher
                    gh_res = github_researcher({"github_username": github.strip(), "job_technologies": []})
                    fetched = gh_res.get("github_repos", [])
                    profile_manager.update_cached_github_repos(uid, fetched)
                st.toast(f"{len(fetched)} projeto(s) salvos no cache do seu perfil!", icon=":material/check_circle:")
                st.rerun()
            if repos:
                with st.container(height=320, border=False):
                    for r in repos:
                        lang = f" :gray-badge[{r.get('language')}]" if r.get("language") else ""
                        st.markdown(f"**{r.get('name')}**{lang}  \n:gray[{r.get('description') or 'Sem descrição'}]")
            elif not github.strip():
                st.caption("Preencha o usuário do GitHub acima para buscar seus projetos.")

    with col_main:
        with st.container(border=True):
            st.markdown("#### :material/description: Currículo base")
            st.caption("Ponto de partida de toda nova otimização. Importe um arquivo ou cole o texto.")
            tab_edit, tab_preview = st.tabs([":material/edit: Editar", ":material/visibility: Pré-visualizar"])
            with tab_edit:
                resume = resume_input(key_resume, prof.get("base_resume", ""), height=460)
            with tab_preview:
                with st.container(height=560, border=False):
                    st.markdown(resume or "_Nada para mostrar ainda._")

    # Completude e salvamento
    checks = {
        "Nome": bool(name.strip()),
        "GitHub": bool(github.strip()),
        "Currículo base": bool(resume.strip()),
        "Projetos em cache": bool(repos),
    }
    done = sum(checks.values())
    missing = [label for label, ok in checks.items() if not ok]
    dirty = (name, github, resume) != (prof.get("full_name", ""), prof.get("github_username", ""), prof.get("base_resume", ""))

    with summary, st.container(border=True):
        c_avatar, c_info, c_progress, c_save = st.columns([0.6, 2.4, 2, 1.3], vertical_alignment="center")
        with c_avatar:
            st.markdown(f'<div class="gm-avatar">{_initials(name, email)}</div>', unsafe_allow_html=True)
        with c_info:
            st.markdown(f"### {name or 'Seu nome'}", anchors=False)
            handle = f" · :material/alternate_email: {github}" if github else ""
            st.caption(f":material/mail: {email}{handle}")
        with c_progress:
            st.progress(done / len(checks), text=f"Perfil {int(100 * done / len(checks))}% completo")
            st.caption(f"Falta: {', '.join(missing)}" if missing else ":green[:material/check_circle:] Tudo pronto para otimizar")
        with c_save:
            if st.button("Salvar perfil", type="primary", icon=":material/save:", width="stretch", disabled=not dirty, key="btn_save_profile"):
                clear_transient_state()
                profile_manager.save_user_profile(uid, {
                    "email": email,
                    "full_name": name,
                    "github_username": github,
                    "base_resume": resume,
                    "cached_repos": repos,
                    "skills": prof.get("skills", [])
                })
                st.toast("Perfil salvo com sucesso!", icon=":material/check_circle:")
                st.rerun()
            st.caption(":orange[:material/edit:] Alterações não salvas" if dirty else ":material/cloud_done: Tudo salvo", text_alignment="center")
