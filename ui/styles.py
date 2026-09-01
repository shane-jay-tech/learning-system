import streamlit as st


_CSS = """
<style>
:root {
  --primary: #5B5BD6;
  --primary-dark: #4547B9;
  --primary-soft: #EEEEFF;
  --accent: #168B70;
  --danger: #C83E4D;
  --warning: #B76E00;
  --bg: #F5F6FA;
  --surface: #FFFFFF;
  --surface-muted: #F8F9FC;
  --text: #172033;
  --muted: #667085;
  --border: #DDE2EA;
  --border-strong: #C8CFDB;
  --shadow-sm: 0 1px 2px rgba(23, 32, 51, .05);
  --shadow-md: 0 8px 24px rgba(23, 32, 51, .08);
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
}

html, body, [class*="css"] {
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
               "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Arial,
               sans-serif !important;
  -webkit-font-smoothing: auto;
  text-rendering: optimizeLegibility;
}

html { font-size: 16px; }
.stApp { background: var(--bg); }

/* 主内容：修正 Streamlit 默认 80px 横向内边距，在普通笔记本上释放有效宽度。 */
[data-testid="stMainBlockContainer"] {
  max-width: 1440px;
  padding: 2rem clamp(1.25rem, 3vw, 3rem) 4rem;
}

.stMain [data-testid="stMarkdownContainer"] { color: var(--text); }
.stMain [data-testid="stMarkdownContainer"] p,
.stMain [data-testid="stMarkdownContainer"] li {
  font-size: 1rem;
  line-height: 1.72;
}
.stMain [data-testid="stMarkdownContainer"] h1,
.stMain [data-testid="stMarkdownContainer"] h2,
.stMain [data-testid="stMarkdownContainer"] h3 {
  color: var(--text);
  font-weight: 700;
  letter-spacing: -.015em;
  line-height: 1.3;
}
.stMain [data-testid="stMarkdownContainer"] h1 { font-size: 1.85rem; }
.stMain [data-testid="stMarkdownContainer"] h2 { font-size: 1.45rem; }
.stMain [data-testid="stMarkdownContainer"] h3 { font-size: 1.12rem; }
.stMain [data-testid="stCaptionContainer"] {
  color: var(--muted);
  font-size: .875rem;
  line-height: 1.55;
}

/* 侧栏：低刺激浅色工作区，当前项通过柔和紫色高亮。 */
section[data-testid="stSidebar"] {
  background: #F8F8FC;
  border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding-top: .8rem; }
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] [data-testid="stVerticalBlock"] {
  gap: .42rem !important;
}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: var(--muted); }
.sidebar-brand { display: flex; align-items: center; gap: 10px; padding: 4px 4px 2px; }
.sidebar-brand-mark {
  display: grid; place-items: center; width: 34px; height: 34px;
  border: 1px solid #CFCFF6; border-radius: 10px; background: var(--primary-soft);
  color: var(--primary-dark); font-size: 17px; font-weight: 800;
}
.sidebar-brand-name { color: var(--text); font-size: 1rem; font-weight: 750; }
.sidebar-brand-meta { color: var(--muted); font-size: .75rem; margin-top: 1px; }
.sidebar-label {
  color: #7A8497; font-size: .72rem; font-weight: 700; letter-spacing: .08em;
  margin: 1.1rem 4px .4rem;
}
.sidebar-foot { color: #7A8497; font-size: .76rem; line-height: 1.55; padding: 2px 4px; }
section[data-testid="stSidebar"] hr { border-color: #E6E8EF; margin: .85rem 0; }
section[data-testid="stSidebar"] .stButton > button {
  min-height: 42px; justify-content: flex-start; background: transparent;
  border: 1px solid transparent; border-radius: 10px; color: #3B4559;
  font-weight: 560; padding: 8px 12px; text-align: left;
  transition: background-color .12s ease, border-color .12s ease, color .12s ease;
}
section[data-testid="stSidebar"] .stButton > button:hover {
  background: #F0F1F7; border-color: #E2E5ED; color: var(--text);
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
  background: var(--primary-soft) !important; border: 1px solid #D0D1F7 !important;
  color: var(--primary-dark) !important; box-shadow: none !important;
}
section[data-testid="stSidebar"] [data-testid="stSelectbox"] label p {
  color: #5C667A; font-size: .78rem; font-weight: 700;
}

/* 页面标题：保留品牌色，但避免大面积高饱和渐变。 */
.hero {
  position: relative; overflow: hidden;
  background: linear-gradient(180deg, #FFFFFF 0%, #FAFAFE 100%);
  border: 1px solid var(--border); border-left: 4px solid var(--primary);
  border-radius: var(--radius-lg); padding: 24px 28px; color: var(--text);
  margin-bottom: 24px; box-shadow: var(--shadow-sm);
}
.hero::after {
  content: ""; position: absolute; width: 150px; height: 150px; right: -72px;
  top: -82px; border-radius: 50%; background: rgba(91, 91, 214, .07);
}
.hero h1 {
  color: var(--text); margin: 0 0 7px; font-size: clamp(1.55rem, 2vw, 1.9rem);
  line-height: 1.25; letter-spacing: -.02em;
}
.hero p { color: var(--muted); margin: 0; max-width: 72ch; font-size: .95rem; line-height: 1.6; }

.section-title {
  display: flex; align-items: center; gap: 9px; color: #364056; font-size: .94rem;
  font-weight: 750; letter-spacing: .01em; margin: 1.8rem 0 .75rem;
}
.section-title::before {
  content: ""; width: 4px; height: 16px; border-radius: 99px; background: var(--primary);
}
section[data-testid="stSidebar"] .section-title {
  color: #667085; font-size: .74rem; letter-spacing: .08em; margin: 1rem 0 .35rem;
}
section[data-testid="stSidebar"] .section-title::before { height: 13px; width: 3px; }

/* 通用卡片。 */
.stMain [data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--surface); border-color: var(--border) !important;
  border-radius: var(--radius-md) !important; box-shadow: var(--shadow-sm);
}
.lang-card {
  min-height: 150px; background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-md); padding: 18px 20px 16px; margin-bottom: 10px;
  box-shadow: var(--shadow-sm); transition: border-color .12s ease, box-shadow .12s ease;
}
.lang-card:hover { border-color: #BFC1EE; box-shadow: var(--shadow-md); }
.lang-card .head { display: flex; align-items: center; gap: 11px; margin-bottom: 8px; }
.lang-card .icon {
  display: grid; place-items: center; width: 36px; height: 36px; flex: 0 0 36px;
  border-radius: 10px; background: var(--primary-soft); font-size: 18px;
}
.lang-card .title { color: var(--text); font-size: 1.05rem; font-weight: 720; margin: 0; }
.lang-card .subtitle { color: var(--muted); font-size: .86rem; margin: 0 0 13px; line-height: 1.5; }
.lang-card .stat-row {
  display: flex; flex-wrap: wrap; gap: 6px 16px; color: var(--muted); font-size: .8rem;
}
.lang-card .stat-row b { color: #344054; font-weight: 700; }

.metric-tile {
  min-height: 96px; display: flex; flex-direction: column; justify-content: center;
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md);
  padding: 14px 17px; text-align: left; box-shadow: var(--shadow-sm);
}
.metric-tile .num { color: var(--primary-dark); font-size: 1.65rem; font-weight: 760; line-height: 1.15; }
.metric-tile .lbl { color: var(--muted); font-size: .8rem; margin-top: 7px; }
.metric-tile.streak { background: #FFFCF5; border-color: #EADDBF; }
.metric-tile.streak .num { color: #966100; }

.problem-card {
  background: var(--surface); border: 1px solid var(--border);
  border-left: 4px solid var(--border-strong); border-radius: var(--radius-sm);
  padding: 12px 14px; margin: 6px 0;
}
.problem-card.solved { border-left-color: var(--accent); background: #F2FAF7; }
.problem-card.wrong { border-left-color: var(--danger); background: #FFF5F5; }
.problem-card.active { border-left-color: var(--primary); background: var(--primary-soft); }
.problem-card .pt { font-weight: 700; font-size: .9rem; }
.problem-card .ps { color: var(--muted); font-size: .77rem; margin-top: 3px; }

/* 表单与操作：统一 42px 热区，清晰 focus ring。 */
.stButton > button, .stDownloadButton > button, [data-testid="stFileUploaderDropzone"] button {
  min-height: 42px; border-color: var(--border-strong); border-radius: 10px;
  color: #303A4E; font-weight: 650; padding: 8px 16px;
  transition: background-color .12s ease, border-color .12s ease, box-shadow .12s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  border-color: #AAACE5; color: var(--primary-dark); background: #F8F8FF;
}
.stButton > button[kind="primary"] {
  background: var(--primary) !important; border: 1px solid var(--primary) !important;
  color: white !important; box-shadow: 0 2px 6px rgba(91, 91, 214, .2);
}
.stButton > button[kind="primary"]:hover {
  background: var(--primary-dark) !important; border-color: var(--primary-dark) !important;
  box-shadow: 0 4px 10px rgba(69, 71, 185, .22);
}
button:focus-visible, [role="radio"]:focus-visible, input:focus-visible,
textarea:focus-visible, [data-baseweb="select"]:focus-within {
  outline: 3px solid rgba(91, 91, 214, .28) !important; outline-offset: 2px;
}
[data-baseweb="select"] > div, .stTextInput input, .stTextArea textarea {
  min-height: 42px; border-color: var(--border-strong) !important; border-radius: 10px !important;
}

/* 反馈、展开区和标签页。 */
[data-testid="stAlert"] { border-radius: var(--radius-md); border-width: 1px; padding: .8rem 1rem; }
[data-testid="stExpander"] {
  overflow: hidden; border-color: var(--border) !important;
  border-radius: var(--radius-md) !important; background: var(--surface);
}
[data-testid="stExpander"] summary { min-height: 46px; }
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid var(--border); }
.stTabs [data-baseweb="tab"] {
  min-height: 44px; color: var(--muted); font-weight: 650; padding: 0 14px;
}
.stTabs [aria-selected="true"] { color: var(--primary-dark) !important; }
.stProgress > div > div { background-color: var(--primary) !important; }
.stProgress [role="progressbar"] { height: 8px; border-radius: 99px; }
[data-testid="stMetric"] { padding: 3px 0; }
[data-testid="stMetricValue"] { color: #263047; font-size: 1.55rem; }
[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: var(--radius-md); overflow: hidden; }

.lesson-box { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 22px 24px; }
.stMain code {
  background: #EEF1F6; color: #3E4671; padding: 2px 5px; border-radius: 5px;
  font-family: "Cascadia Code", "JetBrains Mono", Consolas, monospace; font-size: .88em;
}
.stMain pre {
  background: #111827; color: #E5E7EB; border-radius: 10px; padding: 14px 16px; overflow-x: auto;
}
.stMain pre code { background: transparent; color: inherit; padding: 0; }
.editor-wrap textarea {
  font-family: "Cascadia Code", "JetBrains Mono", Consolas, monospace !important;
  font-size: 14px !important; line-height: 1.6 !important; background: #111827 !important;
  color: #E5E7EB !important; border: 1px solid #30394B !important; border-radius: 10px !important;
}
.io-box {
  max-height: 240px; overflow: auto; background: #111827; color: #E5E7EB;
  border-radius: 9px; padding: 13px 15px; font-family: "Cascadia Code", Consolas, monospace;
  font-size: .84rem; line-height: 1.6; white-space: pre-wrap; overflow-wrap: anywhere;
}
.io-box.expected { background: var(--surface-muted); color: var(--text); border: 1px solid var(--border); }
.verdict {
  display: flex; align-items: center; gap: 10px; border-radius: var(--radius-md);
  padding: 14px 17px; margin: 14px 0; font-size: .94rem;
}
.verdict.pass { background: #F0F9F6; color: #126B57; border: 1px solid #BEE4D9; }
.verdict.fail { background: #FFF3F3; color: #9D2E3C; border: 1px solid #F2C7CC; }
.verdict .ico { font-size: 18px; }
.ai-feedback {
  background: #FFF8E8; border: 1px solid #F0D7A2; border-left: 4px solid #D28A17;
  border-radius: var(--radius-md); padding: 13px 16px; margin: 12px 0 8px;
  color: #704A0B; line-height: 1.65;
}
.ai-feedback, .ai-feedback * { color: #704A0B !important; }
.ai-feedback .label { font-weight: 750; }

/* Streamlit chrome：保留侧栏恢复按钮，仅隐藏无关动作。 */
[data-testid="stToolbarActions"], [data-testid="stMainMenu"],
[data-testid="stStatusWidget"], [data-testid="stDecoration"] { display: none !important; }
header[data-testid="stHeader"], footer { background: transparent !important; }
#MainMenu { visibility: hidden; }

::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb {
  background: #C8CFDB; border: 2px solid transparent; border-radius: 99px; background-clip: content-box;
}
::-webkit-scrollbar-thumb:hover { background-color: #A8B1C1; }
::-webkit-scrollbar-track { background: transparent; }

@media (max-width: 900px) {
  [data-testid="stMainBlockContainer"] { padding: 1.2rem 1rem 3rem; }
  [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
  [data-testid="stMainBlockContainer"] [data-testid="stColumn"] {
    flex: 1 1 300px !important;
    width: 100% !important;
    min-width: min(100%, 300px) !important;
  }
  .hero { padding: 20px; margin-bottom: 18px; }
  .hero h1 { font-size: 1.5rem; }
  .metric-tile { min-height: 84px; }
  .lang-card { min-height: 0; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    scroll-behavior: auto !important; transition: none !important; animation: none !important;
  }
}
</style>
"""


def inject():
    st.markdown(_CSS, unsafe_allow_html=True)
