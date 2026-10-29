from pathlib import Path
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
import json
import streamlit as st

from src.config_loader import load_settings, load_sources
from src.news_fetcher import fetch_sources
from src.web_discovery import discover_web
from src.deduplicator import deduplicate
from src.story_grouper import group_stories
from src.verification_engine import assess_story
from src.briefing_generator import make_briefing
from src.social_writer import generate_posts
from src.graphic_generator import make_graphic, STYLES
from src.storage import Store
from src.exporters import stories_json, briefing_markdown, social_txt, report_html
from src.article_extractor import extract_article

st.set_page_config(page_title="NewsPilot — The living newsroom", page_icon="◈", layout="wide", initial_sidebar_state="collapsed")

# NewsPilot uses a single dark editorial theme for a consistent newsroom experience.
_dark = True
_palette = {
    "bg": "#07131B" if _dark else "#F5F3EC",
    "surface": "#10232E" if _dark else "#FFFEFA",
    "surface2": "#153542" if _dark else "#E9F1EB",
    "ink": "#F4F8FC" if _dark else "#17252D",
    "muted": "#9CB2C0" if _dark else "#617176",
    "line": "#294653" if _dark else "#D8E0DA",
    "teal": "#58D6C5" if _dark else "#167D73",
    "accent": "#9A8CFF" if _dark else "#7566D8",
    "hero": "linear-gradient(120deg,#0D202C 0%,#123B4A 52%,#17645F 100%)" if _dark else "linear-gradient(125deg,#FFFEFA 0%,#EDF4EE 58%,#D8EBE4 100%)",
    "chipbg": "#163440" if _dark else "#E6F1EB",
    "chipink": "#9AF0E3" if _dark else "#286B63",
}
st.markdown(f'''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&display=swap');
:root{{--paper:{_palette['bg']};--ink:{_palette['ink']};--teal:{_palette['teal']};--sage:{_palette['surface2']};--coral:{_palette['accent']};--muted:{_palette['muted']};--line:{_palette['line']};--surface:{_palette['surface']};}}
html,body,[class*="css"]{{font-family:'DM Sans',sans-serif}}
.stApp{{background:var(--paper);color:var(--ink)}}
.block-container{{max-width:1440px;padding-top:1.25rem;padding-bottom:4rem}}
[data-testid="stHeader"]{{background:transparent}}
[data-testid="stMarkdownContainer"] p{{line-height:1.62}}
h1,h2,h3{{color:var(--ink)!important;letter-spacing:-.025em}}
h1,h2{{font-family:'DM Serif Display',Georgia,serif;font-weight:400}}
h1{{font-size:clamp(2.3rem,4vw,4.2rem)!important;line-height:1.02!important}}
h2{{font-size:clamp(1.7rem,2.5vw,2.5rem)!important}}
.np-brand{{display:flex;align-items:center;gap:10px;font-weight:700;letter-spacing:.13em;font-size:.83rem;color:var(--ink);text-transform:uppercase}}
.np-mark{{width:18px;height:22px;display:inline-block;position:relative;border:2px solid var(--teal);border-radius:3px;background:linear-gradient(180deg,#173D49,#102832);box-shadow:4px 3px 0 -1px #F2C879;animation:mark-pop 3.2s ease-in-out infinite}}.np-mark:before{{content:"";position:absolute;left:3px;right:3px;top:5px;height:2px;background:var(--teal);box-shadow:0 4px 0 #9CB2C0,0 8px 0 #9CB2C0}}
.np-hero{{position:relative;overflow:hidden;background:{_palette['hero']};border:1px solid #58D6C54D;border-radius:24px;padding:clamp(30px,4.4vw,62px);margin:14px 0 24px;min-height:270px;box-shadow:0 22px 70px #00000030,inset 0 1px 0 #ffffff0b;isolation:isolate;animation:hero-enter .65s cubic-bezier(.2,.8,.2,1) both}}
.np-hero:before{{content:'';position:absolute;width:340px;height:340px;border:1px solid {_palette['teal']}70;border-radius:50%;right:-75px;top:-165px;box-shadow:0 0 0 32px {_palette['teal']}16,0 0 0 66px {_palette['teal']}0b,0 0 0 105px {_palette['teal']}08;animation:orbit 28s linear infinite;z-index:-1}}
.np-hero:after{{content:'';position:absolute;width:155px;height:155px;border-radius:50%;right:125px;bottom:-105px;background:linear-gradient(145deg,{_palette['accent']}90,#F2C87966);filter:blur(1px);animation:float 6s ease-in-out infinite alternate;z-index:-1}}
.np-hero-inner{{position:relative;z-index:1;max-width:780px}}
.np-kicker,.np-eyebrow{{font-size:.73rem;letter-spacing:.14em;text-transform:uppercase;color:var(--teal);font-weight:700;margin-bottom:14px}}
.np-sub{{max-width:620px;color:{_palette['muted']};font-size:1.08rem}}
.np-rule{{height:1px;background:var(--line);margin:22px 0 28px}}
.np-article{{border:1px solid #31515a99;background:linear-gradient(145deg,#12262fe8,#0f2028f2);backdrop-filter:blur(14px);border-radius:16px;padding:22px;margin:14px 0;box-shadow:0 12px 34px #00000018;transition:transform .22s ease,border-color .22s ease,box-shadow .22s ease}}.np-article:hover{{transform:translateY(-2px);border-color:#54c4b177;box-shadow:0 18px 38px #00000026}}
.np-small{{font-size:.82rem;color:var(--muted)}}
.np-chip{{display:inline-block;border:1px solid var(--line);background:{_palette['chipbg']};color:{_palette['chipink']};border-radius:999px;padding:6px 11px;font-size:.72rem;letter-spacing:.04em;text-transform:uppercase}}
.stTabs [data-baseweb="tab-list"]{{gap:8px;border-bottom:1px solid var(--line)}}
.stTabs [data-baseweb="tab"]{{height:48px;padding:0 14px;color:{_palette['muted']}!important;font-weight:700!important;background:transparent!important}}
.stTabs [data-baseweb="tab"] p{{color:inherit!important}}
.stTabs [data-baseweb="tab"][aria-selected="true"]{{color:var(--teal)!important;border-bottom:3px solid var(--teal)!important}}
.stTabs [data-baseweb="tab-highlight"]{{background-color:var(--teal)!important}}
.stTabs [data-baseweb="tab-border"]{{background-color:var(--line)!important}}
.stRadio label,.stCheckbox label,.stSelectbox label,.stTextInput label,.stTextArea label{{color:var(--ink)!important}}
.stTextInput input,.stTextArea textarea{{color:var(--ink)!important;background:var(--surface)!important}}
.stTextInput input::placeholder,.stTextArea textarea::placeholder{{color:var(--muted)!important;opacity:1!important}}
.stSelectbox [data-baseweb="select"] *{{color:var(--ink)!important}}
.stButton button,.stDownloadButton button{{color:var(--ink)!important;border-radius:9px!important;border:1px solid var(--line)!important;background:var(--surface)!important;transition:all .18s ease}}
.stButton button:hover,.stDownloadButton button:hover{{border-color:var(--teal)!important;transform:translateY(-1px)}}
[data-testid="stRadio"] [role="radiogroup"]{{gap:8px}}[data-testid="stRadio"] label{{background:#12262f;border:1px solid #31515a;border-radius:999px;padding:7px 14px;transition:all .18s ease}}[data-testid="stRadio"] label:has(input:checked){{border-color:#54c4b1;background:#193740}}
button[kind="primary"]{{background:linear-gradient(105deg,#58D6C5,#9A8CFF)!important;border:1px solid #58D6C5!important;border-radius:12px!important;font-weight:700!important;color:#07131B!important}}
[data-testid="stBaseButton-primary"],[data-testid="stBaseButton-primary"] p{{background:linear-gradient(105deg,#5DE0C5 0%,#76B7FF 58%,#B7A4FF 100%)!important;background-color:#5DE0C5!important;color:#071820!important;border-color:#83E9DB!important;border-radius:12px!important;font-weight:700!important}}
[data-testid="stBaseButton-primary"]:hover{{filter:saturate(1.1);box-shadow:0 12px 28px #58D6C52b!important;transform:translateY(-2px)}}
input[type="radio"],input[type="checkbox"]{{accent-color:#58D6C5!important}}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-testid="stSelectbox"]>div>div{{border-radius:9px!important;background:var(--surface)!important;border-color:var(--line)!important}}
[data-testid="stMetric"]{{background:var(--surface);border:1px solid var(--line);padding:17px 19px;border-radius:12px}}
[data-testid="stMetricLabel"], [data-testid="stCaptionContainer"]{{color:var(--muted)!important}}
[data-testid="stMetricValue"]{{color:var(--ink)!important}}
[data-testid="stExpander"]{{border:1px solid var(--line);border-radius:10px;background:var(--surface)}}
.np-loader{{display:flex;align-items:center;gap:16px;padding:18px 20px;margin:12px 0 18px;border:1px solid var(--line);border-radius:12px;background:{_palette['surface2']};animation:shimmer 2.6s linear infinite}}
.np-orbit{{width:38px;height:38px;flex:0 0 38px;border:2px solid var(--teal);border-radius:50%;position:relative;animation:spin 2s linear infinite}}
.np-orbit:after{{content:'';position:absolute;left:14px;top:-4px;width:8px;height:8px;border-radius:50%;background:var(--coral);box-shadow:0 0 0 5px {_palette['accent']}22}}
.np-loader-title{{font-weight:700;color:var(--ink)}}.np-loader-sub{{font-size:.86rem;color:var(--muted);margin-top:3px}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}@keyframes shimmer{{to{{background-position:200% 50%}}}}@keyframes orbit{{to{{transform:rotate(360deg)}}}}@keyframes float{{to{{transform:translateY(-18px)}}}}
/* Discover search panel: elevated, focused, editorial */
[data-testid="stForm"]{{background:linear-gradient(135deg,#102A35 0%,#132A3D 55%,#202B45 100%);border:1px solid #3E6976;border-radius:22px;padding:20px 20px 16px;box-shadow:0 18px 48px #00000026;transition:border-color .25s ease,box-shadow .25s ease,transform .25s ease}}
[data-testid="stForm"]:focus-within{{border-color:#58D6C5;box-shadow:0 0 0 3px #58D6C51b,0 20px 46px #0000002a;transform:translateY(-2px)}}
[data-testid="stForm"] [data-testid="stTextInput"] input{{min-height:50px;font-size:1rem;border-radius:12px!important}}
[data-testid="stFormSubmitButton"] button,[data-testid="stForm"] button[kind="primary"],[data-testid="stForm"] button{{min-height:50px;background:linear-gradient(105deg,#5DE0C5 0%,#76B7FF 58%,#B7A4FF 100%)!important;background-color:#5DE0C5!important;border:1px solid #83E9DB!important;border-radius:12px!important;box-shadow:0 8px 26px #55DCC51f;color:#071820!important;font-weight:700!important;transition:transform .22s ease,box-shadow .22s ease,filter .22s ease}}
[data-testid="stFormSubmitButton"] button p,[data-testid="stForm"] button p{{color:#071820!important;font-weight:700!important}}
[data-testid="stFormSubmitButton"] button:hover,[data-testid="stForm"] button:hover{{transform:translateY(-2px);box-shadow:0 14px 30px #58D6C52b;filter:saturate(1.08)}}
[data-testid="stVerticalBlock"] [data-testid="stButton"] button{{transition:transform .2s ease,border-color .2s ease,background .2s ease,box-shadow .2s ease}}
[data-testid="stVerticalBlock"] [data-testid="stButton"] button:hover{{transform:translateY(-2px);box-shadow:0 8px 20px #00000020}}
.np-topic-intro{{padding:3px 0 8px}}
.np-loader{{display:flex;align-items:center;gap:16px;padding:19px 21px;margin:14px 0 20px;border:1px solid #3C777D;border-radius:16px;background:linear-gradient(110deg,#102630,#153A43,#102630);background-size:220% 100%;box-shadow:0 14px 36px #0000002b;animation:loader-glow 2.4s ease-in-out infinite,loader-enter .35s ease-out both}}
.np-news-icon{{width:54px;height:48px;position:relative;flex:0 0 54px;display:grid;place-items:center}}
.np-paper{{position:absolute;width:29px;height:36px;border:2px solid #58D6C5;border-radius:4px;background:#102630;box-shadow:4px 3px 0 #FF6B61;animation:paper-search 1.8s ease-in-out infinite}}
.np-paper:before{{content:"";position:absolute;left:5px;right:5px;top:7px;height:3px;background:#F2C879;box-shadow:0 7px 0 #9CB2C0,0 13px 0 #9CB2C0}}
.np-lens{{position:absolute;width:17px;height:17px;border:3px solid #F4F8FC;border-radius:50%;right:2px;bottom:2px;background:#163440;animation:lens-scan 1.8s ease-in-out infinite}}
.np-lens:after{{content:"";position:absolute;width:8px;height:3px;background:#F4F8FC;right:-6px;bottom:-3px;transform:rotate(45deg);border-radius:2px}}
.np-loader-title{{font-weight:700;color:var(--ink);letter-spacing:-.01em}}.np-loader-sub{{font-size:.86rem;color:var(--muted);margin-top:4px}}
.np-loader-overlay{{position:fixed;inset:0;z-index:999999;background:rgba(4,13,20,.88);backdrop-filter:blur(14px);display:grid;place-items:center;padding:24px;animation:loader-enter .25s ease-out both}}
.np-loader-modal{{width:min(460px,92vw);padding:34px 30px 30px;text-align:center;border-radius:26px;border:1px solid #58D6C566;background:linear-gradient(145deg,#112B37,#0B1C27 68%,#18233A);box-shadow:0 28px 100px #0009,0 0 70px #58D6C51a}}
.np-loader-stage{{height:100px;display:grid;place-items:center;margin-bottom:12px;position:relative}}
.np-loader-stage .np-paper{{width:48px;height:62px;border-width:2px;border-radius:6px;box-shadow:6px 5px 0 #9A8CFF;left:calc(50% - 30px);top:16px}}
.np-loader-stage .np-paper:before{{left:8px;right:8px;top:11px;height:3px;background:#F2C879;box-shadow:0 9px 0 #9CB2C0,0 18px 0 #9CB2C0,0 27px 0 #9CB2C0}}
.np-loader-stage .np-lens{{width:28px;height:28px;border-width:4px;right:calc(50% - 39px);bottom:12px}}
.np-loader-stage .np-lens:after{{width:13px;height:4px;right:-9px;bottom:-5px}}
.np-loader-progress{{height:4px;width:100%;overflow:hidden;background:#294653;border-radius:999px;margin-top:22px}}
.np-loader-progress:after{{content:"";display:block;width:38%;height:100%;border-radius:999px;background:linear-gradient(90deg,#58D6C5,#9A8CFF,#F2C879);animation:progress-scan 1.35s ease-in-out infinite}}
@keyframes progress-scan{{0%{{transform:translateX(-110%)}}100%{{transform:translateX(280%)}}}}
@media(prefers-reduced-motion:reduce){{.np-loader-overlay,.np-loader-progress:after{{animation:none}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}@keyframes shimmer{{to{{background-position:200% 50%}}}}@keyframes orbit{{to{{transform:rotate(360deg)}}}}@keyframes float{{to{{transform:translateY(-18px)}}}}
@keyframes mark-pop{{0%,100%{{transform:translateY(0) rotate(0)}}50%{{transform:translateY(-2px) rotate(-3deg)}}}}
@keyframes hero-enter{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes loader-enter{{from{{opacity:0;transform:translateY(8px) scale(.985)}}to{{opacity:1;transform:translateY(0) scale(1)}}}}
@keyframes loader-glow{{0%,100%{{background-position:0% 50%;border-color:#315763}}50%{{background-position:100% 50%;border-color:#58D6C5}}}}
@keyframes paper-search{{0%,100%{{transform:translate(-3px,1px) rotate(-7deg)}}50%{{transform:translate(3px,-2px) rotate(5deg)}}}}
@keyframes lens-scan{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(-5px,-4px)}}}}
@media(prefers-reduced-motion:reduce){{.np-hero:before,.np-hero:after,.np-loader,.np-orbit,.np-mark,.np-paper,.np-lens{{animation:none}}}}
@media(max-width:700px){{.np-hero{{padding:24px;min-height:220px}}.np-hero:before{{right:-210px}}.block-container{{padding-left:1rem;padding-right:1rem}}}}
</style>''', unsafe_allow_html=True)

settings = load_settings(); sources = load_sources(); news = settings['news']
for key, default in [('articles', []), ('stories', []), ('verification', {}), ('search_health', []), ('feed_health', []), ('article_texts', {}), ('last_graphics', {}), ('selected_story_id', None)]:
    if key not in st.session_state: st.session_state[key] = default


def process(articles):
    articles = deduplicate(articles)
    stories = group_stories(articles)
    verification = {story.story_id: assess_story(story, freshness_hours=news['freshness_hours']) for story in stories}
    st.session_state.articles = articles
    st.session_state.stories = stories
    st.session_state.verification = verification
    if stories and st.session_state.selected_story_id not in {s.story_id for s in stories}:
        st.session_state.selected_story_id = stories[0].story_id
    try:
        if settings['storage']['enabled']:
            store = Store(settings['storage']['database_path'])
            store.save_articles(articles); store.save_stories(stories)
    except Exception:
        # Session data remains usable if local persistence is unavailable.
        pass


def article_date(article):
    if not article.published_at: return 'Publication date unavailable'
    return article.published_at.strftime('%d %b %Y · %H:%M UTC')


def story_by_id(sid):
    return next((s for s in st.session_state.stories if s.story_id == sid), None)


def find_related_coverage(story, max_results=20):
    """Find additional public news-feed snippets when a publisher blocks article extraction."""
    results, health = discover_web(story.canonical_headline, max_results=max_results)
    stop_words = {'about','after','amid','and','are','for','from','how','into','its','new','the','this','with','what','when','where','who','why'}
    def tokens(value):
        import re
        return {w for w in re.findall(r'[a-z0-9]+', (value or '').casefold()) if len(w) > 2 and w not in stop_words}
    target = tokens(story.canonical_headline)
    existing_urls = {a.canonical_url for a in story.related_articles}
    added = []
    for article in results:
        if article.canonical_url in existing_urls:
            continue
        overlap = len(target & tokens(article.title)) / max(1, len(target))
        description = ' '.join((article.description or '').split()).strip()
        if overlap < 0.30 or len(description) < 100 or description.casefold().strip(' .!?') == article.title.casefold().strip(' .!?'):
            continue
        if description.casefold().startswith(article.title.casefold()):
            description = description[len(article.title):].lstrip(' :—–-.')
        if len(description) < 80:
            continue
        article.extracted_text = description
        article.retrieval_status = 'feed_summary'
        story.related_articles.append(article)
        st.session_state.article_texts[article.article_id] = description
        existing_urls.add(article.canonical_url)
        added.append(article)
        if len(added) >= 5:
            break
    return added, health


def go_to_create(story_id, studio_section='Briefing'):
    """Navigation callback runs before widgets are instantiated on rerun."""
    st.session_state['selected_story_id'] = story_id
    st.session_state['active_section'] = 'Create studio'
    st.session_state['active_section_radio'] = 'Create studio'
    st.session_state['studio_tab_choice'] = studio_section
    st.session_state['open_graphic_studio'] = (studio_section == 'Graphic studio')


def make_assets_zip(story, verification, briefing, posts, graphic_path=None, caption=''):
    buffer = BytesIO()
    with ZipFile(buffer, 'w', ZIP_DEFLATED) as archive:
        archive.writestr('briefing.md', briefing_markdown(story, verification, briefing))
        archive.writestr('social_drafts.txt', social_txt(posts))
        archive.writestr('story.json', stories_json([story]))
        archive.writestr('report.html', report_html(story, verification, briefing))
        archive.writestr('share_caption.txt', caption)
        if graphic_path and Path(graphic_path).exists(): archive.write(graphic_path, 'graphic.png')
    return buffer.getvalue()

st.markdown('<div class="np-brand"><span class="np-mark"></span> NEWSPILOT <span style="font-weight:400;color:var(--muted);letter-spacing:.05em">/ THE LIVING NEWSROOM</span></div>', unsafe_allow_html=True)
st.markdown('''<div class="np-hero"><div class="np-hero-inner"><div class="np-kicker">Independent news intelligence</div><h1>Understand the story<br>behind the headlines.</h1><p class="np-sub">Discover reporting, compare coverage, and turn what you learn into clear editorial content — all in one calm, focused workspace.</p></div></div>''', unsafe_allow_html=True)
st.caption('Explore the news · Read across sources · Create content you can review before sharing')

if 'active_section' not in st.session_state:
    st.session_state.active_section = 'Discover'
if 'active_section_radio' not in st.session_state:
    st.session_state['active_section_radio'] = st.session_state.get('active_section', 'Discover')
active_section = st.radio('Newsroom', ['Discover', 'Coverage review', 'Create studio'], horizontal=True, key='active_section_radio', label_visibility='collapsed')
st.session_state['active_section'] = active_section

if active_section == 'Discover':
        st.markdown('<div class="np-eyebrow">THE NEWS DESK · DISCOVER</div>', unsafe_allow_html=True)
        st.subheader('What is happening in the world?')
        st.caption('Search a topic to surface current reporting, compare coverage, and create something useful from a story.')
        with st.form('search_form', clear_on_submit=False):
            qcol, ncol = st.columns([4,1])
            with qcol: query = st.text_input('Search topic', placeholder='Try cybersecurity in India, climate change, elections…', label_visibility='collapsed')
            with ncol: limit = st.selectbox('Results', [20, 50, 100], index=1, label_visibility='collapsed')
            submitted = st.form_submit_button('Search coverage  →', type='primary', use_container_width=True)
        st.markdown('<div class="np-rule"></div><div class="np-eyebrow">EXPLORE A BEAT</div>', unsafe_allow_html=True)
        st.caption('Jump into a newsroom beat, then sort the coverage by trending or publication time.')
        trending_topics = [
            ('AI & technology', 'artificial intelligence technology'),
            ('India', 'India latest news'),
            ('Cybersecurity', 'cybersecurity'),
            ('Climate', 'climate change'),
            ('World affairs', 'world news'),
            ('Business & markets', 'business markets'),
        ]
        topic_cols = st.columns(6)
        picked_topic = None
        for topic_idx, (topic_label, topic_query) in enumerate(trending_topics):
            with topic_cols[topic_idx]:
                if st.button(topic_label, key=f'trend-topic-{topic_idx}', use_container_width=True):
                    picked_topic = topic_query
        if picked_topic:
            query = picked_topic
            submitted = True
        if submitted:
            if not query.strip(): st.warning('Enter a topic or keyword to start your search.')
            else:
                loader = st.empty()
                loader.markdown('<div class="np-loader-overlay"><div class="np-loader-modal"><div class="np-eyebrow">NEWSPILOT · LIVE SEARCH</div><div class="np-loader-stage"><span class="np-paper"></span><span class="np-lens"></span></div><div class="np-loader-title">Scanning the news desk…</div><div class="np-loader-sub">Searching newspapers, comparing reports, and gathering the latest coverage.</div><div class="np-loader-progress"></div></div></div>', unsafe_allow_html=True)
                try:
                    articles, health = discover_web(query.strip(), int(limit))
                    loader.empty(); st.session_state.search_health = health; process(articles)
                    ok_count = sum(1 for h in health if h.get('ok'))
                    if articles: st.success(f'{len(articles)} reports collected · {ok_count} search providers responded.')
                    elif ok_count == 0: st.error('The news services could not be reached. This is a connection/provider issue, not proof that no news exists. Try again later.')
                    else: st.info('The providers responded but returned no matching reports. Try broader keywords or another spelling.')
                except Exception:
                    loader.empty(); st.error('Search could not be completed. Check your connection and try again.')
        if st.session_state.articles:
            a1, a2, a3 = st.columns(3)
            a1.metric('Reports collected', len(st.session_state.articles)); a2.metric('Related stories', len(st.session_state.stories)); a3.metric('Multi-source groups', sum(1 for v in st.session_state.verification.values() if 'MULTI_SOURCE' in v.get('status','')))
            st.markdown('<div class="np-rule"></div>', unsafe_allow_html=True)
            st.subheader('Latest coverage')
            sort_choice = st.radio('Show stories', ['Trending', 'Most recent'], horizontal=True, label_visibility='collapsed', key='news_sort_order')
            article_story_sizes = {}
            for grouped_story in st.session_state.stories:
                for grouped_article in grouped_story.related_articles:
                    article_story_sizes[grouped_article.article_id] = len(grouped_story.related_articles)
            if sort_choice == 'Trending':
                ordered_articles = sorted(st.session_state.articles, key=lambda a: (article_story_sizes.get(a.article_id, 1), a.published_at.timestamp() if a.published_at else 0), reverse=True)
            else:
                ordered_articles = sorted(st.session_state.articles, key=lambda a: a.published_at.timestamp() if a.published_at else 0, reverse=True)
            for idx, article in enumerate(ordered_articles[:30]):
                with st.container():
                    st.markdown('<div class="np-article">', unsafe_allow_html=True)
                    st.markdown(f'<div class="np-eyebrow">{article.category or "News"} &nbsp; / &nbsp; {article.publisher_name}</div>', unsafe_allow_html=True)
                    st.markdown(f'### {article.title}')
                    st.caption(article_date(article))
                    full_text = st.session_state.article_texts.get(article.article_id) or article.extracted_text
                    preview = full_text or article.description
                    if preview and preview.strip().casefold().strip(' .!?') == article.title.strip().casefold().strip(' .!?'):
                        preview = ''
                    if preview:
                        st.write(preview[:900] + ('…' if len(preview) > 900 else ''))
                    else:
                        st.caption('The publisher feed only supplied the headline. Open “Read more / retrieve text” below to try retrieving the article body for a useful summary.')
                    action1, action2, action3 = st.columns([1,1,1])
                    with action1:
                        st.markdown(f'[Read original report ↗]({article.canonical_url})')
                    related_story = next((candidate for candidate in st.session_state.stories if any(a.article_id == article.article_id for a in candidate.related_articles)), None)
                    with action2:
                        if related_story:
                            st.button('Create story', key=f'create-story-{article.article_id}', use_container_width=True, type='primary', on_click=go_to_create, args=(related_story.story_id, 'Briefing'))
                        else:
                            st.button('Create story', key=f'create-story-{article.article_id}', use_container_width=True, type='primary', disabled=True)
                    with action3:
                        if related_story:
                            st.button('Create image', key=f'create-image-{article.article_id}', use_container_width=True, on_click=go_to_create, args=(related_story.story_id, 'Graphic studio'))
                        else:
                            st.button('Create image', key=f'create-image-{article.article_id}', use_container_width=True, disabled=True)
                    with st.expander('Read more / retrieve text'):
                            if full_text:
                                st.write(full_text)
                                st.download_button('Download article text', full_text, file_name=f'article-{article.article_id}.txt', mime='text/plain', key=f'article-download-{article.article_id}')
                            else:
                                st.caption('Some publishers restrict extraction or require a subscription. Only text actually retrieved will be shown.')
                                if st.button('Retrieve available article text', key=f'extract-{article.article_id}'):
                                    try:
                                        with st.spinner('Retrieving readable article text…'):
                                            extracted = extract_article(article.canonical_url)
                                        st.session_state.article_texts[article.article_id] = extracted
                                        article.extracted_text = extracted
                                        st.session_state['extract_status_'+article.article_id] = 'Retrieved' if len(extracted) >= 250 else 'Partial or unavailable'
                                        st.rerun()
                                    except Exception:
                                        st.error('This publisher could not be retrieved. The site may restrict access, use scripts, or require a subscription.')
                            status = st.session_state.get('extract_status_'+article.article_id)
                            if status: st.caption('Retrieval status: ' + status)
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info('Search a topic or choose a suggestion above to see related news stories here.')

if active_section == 'Coverage review':
        st.markdown('<div class="np-eyebrow">Read across publishers</div>', unsafe_allow_html=True)
        st.subheader('Coverage review')
        st.caption('Groups describe reporting availability. They do not establish that a claim is true.')
        stories = st.session_state.stories
        if not stories: st.info('Search for a topic in Discover first. Related stories will appear here.')
        else:
            filter_text = st.text_input('Filter stories', placeholder='Search story headlines…', key='story_filter')
            for story in stories:
                if filter_text and filter_text.lower() not in story.canonical_headline.lower(): continue
                v = st.session_state.verification.get(story.story_id, {})
                with st.container():
                    st.markdown('<div class="np-article">', unsafe_allow_html=True)
                    st.markdown(f'## {story.canonical_headline}')
                    domains = {a.publisher_domain for a in story.related_articles if a.publisher_domain}
                    st.caption(f'{len(story.related_articles)} report(s) · {len(domains)} publisher domain(s) · latest: {max((a.published_at for a in story.related_articles if a.published_at), default=None).strftime("%d %b %Y %H:%M UTC") if any(a.published_at for a in story.related_articles) else "date unavailable"}')
                    st.markdown(f'<span class="np-chip">{v.get("status", "INSUFFICIENT_EVIDENCE").replace("_", " ").title()}</span>', unsafe_allow_html=True)
                    for a in story.related_articles[:8]:
                        st.markdown(f'- [{a.publisher_name}: {a.title}]({a.canonical_url})')
                    with st.expander('What this coverage can and cannot tell us'):
                        st.write('Coverage reflects available reporting, not whether a claim is true.')
                        for limitation in v.get('limitations', []): st.write('• ' + str(limitation))
                        if v.get('source_independence'):
                            st.caption('Publisher overlap is considered when comparing coverage; more links alone do not prove a story is accurate.')
                    st.button('Create content from this story →', key='create-from-'+story.story_id, type='primary', on_click=go_to_create, args=(story.story_id, 'Briefing'))
                    st.markdown('</div>', unsafe_allow_html=True)

if active_section == 'Create studio':
        st.markdown('<div class="np-eyebrow">From research to publication-ready assets</div>', unsafe_allow_html=True)
        st.subheader('Create studio')
        stories = st.session_state.stories
        if not stories: st.info('Discover a story first. Your selection will stay with you as you create content.')
        else:
            ids = [s.story_id for s in stories]
            current_id = st.session_state.selected_story_id if st.session_state.selected_story_id in ids else ids[0]
            chosen_id = st.selectbox('Story you are working on', ids, index=ids.index(current_id), format_func=lambda x: next((s.canonical_headline for s in stories if s.story_id == x), x), key='studio_story_select')
            st.session_state.selected_story_id = chosen_id
            story = story_by_id(chosen_id); verification = st.session_state.verification.get(chosen_id, {})
            # Keep the selected story's article objects in sync with text retrieved during this session.
            # Some grouping/storage paths may hold a different Article instance from the Discover view.
            for related_article in story.related_articles:
                retrieved_text = st.session_state.article_texts.get(related_article.article_id)
                if retrieved_text:
                    related_article.extracted_text = retrieved_text
            lead = story.related_articles[0] if story.related_articles else None
            briefing = make_briefing(story, verification)
            st.markdown(f'**Selected story:** {story.canonical_headline}')
            studio_options = ['Briefing', 'Social posts', 'Graphic studio']
            if st.session_state.pop('open_graphic_studio', False):
                st.session_state['studio_tab_choice'] = 'Graphic studio'
            studio_tab = st.radio('Studio section', studio_options, horizontal=True, key='studio_tab_choice', label_visibility='collapsed')
            if studio_tab == 'Briefing':
                st.markdown('### A clear view of the story')
                available_text = (st.session_state.article_texts.get(lead.article_id) or lead.extracted_text) if lead else ''
                st.write(briefing.get('summary', 'Limited source detail is available. Open the original report for more context.'))
                if available_text:
                    with st.expander('View retrieved article text'):
                        st.write(available_text[:12000])
                st.info(briefing.get('note', 'Review the original report before using.'))
                if lead and not (st.session_state.article_texts.get(lead.article_id) or lead.extracted_text):
                    if st.button('Retrieve article text for a detailed summary', key=f'retrieve-briefing-{chosen_id}', use_container_width=True):
                        try:
                            with st.spinner('Retrieving readable article text from the publisher…'):
                                extracted = extract_article(lead.canonical_url)
                            st.session_state.article_texts[lead.article_id] = extracted
                            lead.extracted_text = extracted
                            st.success('Article text retrieved. The briefing and graphic supporting text have been refreshed.')
                            st.rerun()
                        except Exception as exc:
                            st.warning(f'Could not retrieve this publisher’s article text ({type(exc).__name__}). The site may block automated access or require a subscription. Open the original report or try another source.')
                st.markdown('**Collected sources**')
                for src in verification.get('sources', []): st.markdown(f'- [{src.get("publisher", "Publisher")}]({src.get("url", "")})')
                st.download_button('Download briefing (.md)', briefing_markdown(story, verification, briefing), file_name='newspilot-briefing.md', mime='text/markdown', use_container_width=True)
            if studio_tab == 'Social posts':
                st.caption('Editable drafts only. Review facts and links before publishing.')
                posts = generate_posts(story, briefing)
                clean_posts = {k:v for k,v in posts.items() if not k.startswith('_') and isinstance(v,str)}
                edited_posts = {}
                for platform, content in clean_posts.items():
                    edited_posts[platform] = st.text_area(platform, content, key=f'draft-{chosen_id}-{platform}', height=130)
                    st.caption(f'{len(edited_posts[platform])} characters')
                    st.download_button(f'Download {platform} draft', edited_posts[platform], file_name=f'newspilot-{platform.lower().replace(" ","-")}.txt', mime='text/plain', key=f'dl-post-{chosen_id}-{platform}')
                st.download_button('Download all social drafts (.txt)', social_txt(edited_posts), file_name='newspilot-social-drafts.txt', mime='text/plain', use_container_width=True)
            if studio_tab == 'Graphic studio':
                st.write('Create a high-resolution editorial graphic. Choose a visual direction and canvas, then generate a PNG you can download.')
                left, right = st.columns([1,1.15], gap='large')
                with left:
                    headline = st.text_area('Graphic headline', story.canonical_headline, key=f'graphic-head-{chosen_id}', height=100)
                    summary_key = f'graphic-summary-{chosen_id}'
                    default_summary = briefing.get('summary', '')
                    # Refresh stale widget state when it contains only the headline/feed snippet.
                    # Streamlit otherwise preserves the old value even when the default changes.
                    saved_summary = str(st.session_state.get(summary_key, '') or '').strip()
                    short_source_values = {
                        story.canonical_headline.strip().casefold(),
                        (lead.description or '').strip().casefold() if lead else '',
                    }
                    if not saved_summary or saved_summary.casefold() in short_source_values:
                        st.session_state[summary_key] = default_summary
                    available_text = (st.session_state.article_texts.get(lead.article_id) or lead.extracted_text) if lead else ''
                    if lead and not available_text:
                        if st.button('Retrieve article text for a detailed description', key=f'retrieve-graphic-{chosen_id}', use_container_width=True):
                            try:
                                with st.spinner('Retrieving readable article text from the publisher…'):
                                    extracted = extract_article(lead.canonical_url)
                                st.session_state.article_texts[lead.article_id] = extracted
                                lead.extracted_text = extracted
                                st.session_state[summary_key] = make_briefing(story, verification).get('summary', default_summary)
                                st.success('Article text retrieved. The supporting description has been refreshed.')
                                st.rerun()
                            except Exception as exc:
                                st.warning(f'Could not retrieve this publisher’s article text ({type(exc).__name__}). The publisher may block automated access or require a subscription. Open the original report or try another source.')
                    if st.button('Search related coverage for more detail', key=f'coverage-graphic-{chosen_id}', use_container_width=True):
                        try:
                            with st.spinner('Searching public news feeds for additional reporting…'):
                                added, health = find_related_coverage(story)
                            if added:
                                refreshed = make_briefing(story, verification).get('summary', default_summary)
                                st.session_state[summary_key] = refreshed
                                st.success(f'Added {len(added)} related coverage snippet(s). Review the sources before publication.')
                                st.rerun()
                            else:
                                st.warning('The search feeds did not return enough detailed text for a reliable summary. Open the original article or select another report with more source text.')
                        except Exception as exc:
                            st.warning(f'Could not find related coverage ({type(exc).__name__}). Check your internet connection and try again.')
                    summary = st.text_area('Supporting text', default_summary, key=summary_key, height=205, help='Uses retrieved article text or available reporting snippets. If the source provides only a headline, NewsPilot will not invent missing details.')
                    category = st.selectbox('Visual style', STYLES, key=f'graphic-style-{chosen_id}')
                    canvas_options = {'Instagram portrait · 1080 × 1350':(1080,1350),'Square · 1080 × 1080':(1080,1080),'Landscape · 1200 × 675':(1200,675),'Story · 1080 × 1920':(1080,1920)}
                    canvas_label = st.selectbox('Canvas size', list(canvas_options), key=f'graphic-canvas-{chosen_id}')
                    if st.button('Generate graphic', type='primary', use_container_width=True, key=f'generate-graphic-{chosen_id}'):
                        try:
                            output = Path(__file__).resolve().parent / settings.get('output_dir','output') / f'{chosen_id}-{category.lower().replace(" ","-").replace("&","and")}.png'
                            make_graphic(headline, summary, lead.publisher_name if lead else 'News source', lead.published_at.date().isoformat() if lead and lead.published_at else '', lead.canonical_url if lead else '', verification.get('status','INSUFFICIENT_EVIDENCE'), str(output), canvas_options[canvas_label], category)
                            st.session_state.last_graphics[chosen_id] = str(output)
                            st.session_state['graphic_generated_'+chosen_id] = True
                            st.success('Graphic generated successfully. Preview and download are ready.')
                            st.session_state['last_graphic_caption_'+chosen_id] = f'{headline}\n\n{summary}\n\nSource: {lead.publisher_name if lead else "News source"}\nRead more: {lead.canonical_url if lead else ""}'
                        except Exception as exc:
                            st.error(f'The graphic could not be rendered: {type(exc).__name__}: {exc}')
                            st.caption('Check that Pillow is installed and that the output folder is writable, then try again.')
                with right:
                    path = st.session_state.last_graphics.get(chosen_id)
                    if path and Path(path).exists():
                        st.image(path, caption='Preview · locally rendered editorial graphic', use_container_width=True)
                        st.download_button('Download PNG', Path(path).read_bytes(), file_name=Path(path).name, mime='image/png', use_container_width=True)
                        caption = st.text_area('Caption to share', st.session_state.get('last_graphic_caption_'+chosen_id,''), key=f'caption-edit-{chosen_id}', height=125)
                        st.download_button('Download caption (.txt)', caption, file_name='newspilot-caption.txt', mime='text/plain', use_container_width=True)
                        st.caption('To copy, select the caption text and use Ctrl+C. Direct publishing is not enabled.')
                    else:
                        st.markdown('<div class="np-article"><div class="np-eyebrow">Live preview</div><h3>Your story, art-directed.</h3><p class="np-small">Choose a composition and canvas, then generate a high-resolution PNG. Each style has its own visual motif and layout.</p></div>', unsafe_allow_html=True)
