import streamlit as st

_CSS = """
<style>
:root {
  --primary: #6366F1;
  --primary-dark: #4F46E5;
  --accent: #10B981;
  --danger: #EF4444;
  --warning: #F59E0B;
  --bg: #F8FAFC;
  --surface: #FFFFFF;
  --text: #0F172A;
  --muted: #64748B;
  --border: #E2E8F0;
}

html, body, [class*="css"] {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
               "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Helvetica,
               Arial, sans-serif !important;
  color: var(--text);
}

.stApp { background: var(--bg); }

section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #1E1B4B 0%, #312E81 100%);
}
section[data-testid="stSidebar"] * { color: #E0E7FF !important; }
section[data-testid="stSidebar"] .stButton > button {
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.15);
  color: #F1F5F9 !important;
  border-radius: 10px;
  text-align: left;
  padding: 10px 14px;
  font-weight: 500;
  transition: all .15s ease;
}
section[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(255,255,255,0.18);
  border-color: rgba(255,255,255,0.35);
  transform: translateX(2px);
}

.hero {
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
  border-radius: 18px;
  padding: 36px 40px;
  color: white;
  margin-bottom: 28px;
  box-shadow: 0 10px 30px rgba(99,102,241,0.25);
}
.hero h1 { color: white; margin: 0 0 6px 0; font-size: 32px; }
.hero p { color: #E0E7FF; margin: 0; font-size: 15px; }

.lang-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 22px 22px 18px;
  margin-bottom: 16px;
  transition: all .2s ease;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04);
}
.lang-card:hover {
  border-color: var(--primary);
  box-shadow: 0 8px 24px rgba(99,102,241,0.15);
  transform: translateY(-2px);
}
.lang-card .icon { font-size: 32px; margin-bottom: 8px; }
.lang-card .title { font-size: 20px; font-weight: 600; margin: 0 0 4px 0; }
.lang-card .subtitle { color: var(--muted); font-size: 13px; margin: 0 0 14px 0; }
.lang-card .stat-row { display: flex; gap: 16px; font-size: 13px; color: var(--muted); margin-top: 6px; }
.lang-card .stat-row b { color: var(--text); }

.metric-tile {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px 18px;
  text-align: center;
}
.metric-tile .num { font-size: 26px; font-weight: 700; color: var(--primary); }
.metric-tile .lbl { font-size: 12px; color: var(--muted); margin-top: 2px; }

.problem-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 4px solid var(--border);
  border-radius: 10px;
  padding: 12px 14px;
  margin: 6px 0;
  cursor: pointer;
  transition: all .15s ease;
}
.problem-card.solved { border-left-color: var(--accent); background: #ECFDF5; }
.problem-card.wrong  { border-left-color: var(--danger); background: #FEF2F2; }
.problem-card.active { border-left-color: var(--primary); background: #EEF2FF; }
.problem-card .pt { font-weight: 600; font-size: 14px; }
.problem-card .ps { font-size: 12px; color: var(--muted); margin-top: 2px; }

.lesson-box {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px 28px;
}
.lesson-box h1, .lesson-box h2, .lesson-box h3 { color: var(--text); }
.lesson-box code {
  background: #F1F5F9; padding: 2px 6px; border-radius: 4px;
  font-family: "JetBrains Mono", Consolas, "Cascadia Code", monospace;
  font-size: 13px;
}
.lesson-box pre {
  background: #0F172A; color: #E2E8F0; padding: 14px 16px; border-radius: 8px;
  overflow-x: auto;
}
.lesson-box pre code { background: transparent; color: inherit; padding: 0; }
.lesson-box table { border-collapse: collapse; margin: 8px 0; }
.lesson-box th, .lesson-box td { border: 1px solid var(--border); padding: 6px 12px; }
.lesson-box th { background: #F8FAFC; }

.editor-wrap textarea {
  font-family: "JetBrains Mono", Consolas, "Cascadia Code", "SF Mono", monospace !important;
  font-size: 14px !important;
  line-height: 1.55 !important;
  background: #0F172A !important;
  color: #E2E8F0 !important;
  border-radius: 10px !important;
  border: 1px solid var(--border) !important;
}

.verdict {
  border-radius: 12px;
  padding: 16px 20px;
  margin: 14px 0;
  font-size: 15px;
  display: flex; align-items: center; gap: 10px;
}
.verdict.pass { background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; }
.verdict.fail { background: #FEF2F2; color: #991B1B; border: 1px solid #FECACA; }
.verdict .ico { font-size: 22px; }

.io-box {
  background: #0F172A; color: #E2E8F0;
  border-radius: 8px; padding: 12px 14px;
  font-family: "JetBrains Mono", Consolas, monospace;
  font-size: 13px; white-space: pre-wrap; word-break: break-all;
  max-height: 240px; overflow-y: auto;
}
.io-box.expected { background: #F8FAFC; color: var(--text); border: 1px solid var(--border); }

.ai-feedback {
  background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
  border-left: 4px solid var(--warning);
  border-radius: 10px;
  padding: 14px 18px;
  margin: 12px 0;
  color: #78350F;
  line-height: 1.7;
}
.ai-feedback .label { font-weight: 700; margin-bottom: 6px; display: block; }

.section-title {
  font-size: 13px; font-weight: 600; color: var(--muted);
  text-transform: uppercase; letter-spacing: 0.05em;
  margin: 18px 0 8px 0;
}

.stProgress > div > div { background-color: var(--primary) !important; }

.stButton > button[kind="primary"] {
  background: var(--primary) !important;
  border: none !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
  padding: 10px 22px !important;
  transition: all .15s ease;
}
.stButton > button[kind="primary"]:hover {
  background: var(--primary-dark) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99,102,241,0.35);
}

footer, [data-testid="stHeader"] { background: transparent; }
#MainMenu { visibility: hidden; }

/* 桌面 app 模式 — 隐藏部署按钮/主菜单/状态/装饰等 chrome。
   关键经验（实测 playwright 确认）：侧栏收起后的展开按钮 stExpandSidebarButton
   就嵌在 stToolbar 里，所以——
   1) 不要整个隐藏 stToolbar（会连带 display:none 掉展开按钮，导致收起后展不开）；
   2) 不要给 stHeader 设 height:0（会剪掉它）。
   只隐藏 toolbar 里真正的 chrome（actions/菜单），保留 toolbar 容器和顶栏自然高度。 */
[data-testid="stToolbarActions"] { display: none !important; }
[data-testid="stMainMenu"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent !important; }
/* 收紧顶部 padding，让内容更聚焦 */
.main .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
/* 滚动条更精致 */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 5px; }
::-webkit-scrollbar-thumb:hover { background: #94A3B8; }
::-webkit-scrollbar-track { background: transparent; }

/* === 阅读舒适度（用户反馈：字偏小/偏淡，看着累）===
   只作用于主内容区(.block-container)，不动侧栏；放大正文、加深颜色、放宽行高。 */
.block-container [data-testid="stMarkdownContainer"] p,
.block-container [data-testid="stMarkdownContainer"] li {
  font-size: 17px !important;
  line-height: 1.8 !important;
}
.block-container [data-testid="stMarkdownContainer"] { color: #1E293B; }
.block-container [data-testid="stMarkdownContainer"] h1 { font-size: 30px; }
.block-container [data-testid="stMarkdownContainer"] h2 { font-size: 23px; }
.block-container [data-testid="stMarkdownContainer"] h3 { font-size: 19px; }
/* 保护 AI 反馈区/判定条自己的配色，别被上面的深色覆盖 */
.ai-feedback, .ai-feedback * { color: #78350F !important; }
/* 字体渲染：保持 Windows ClearType 次像素（更实），不要 antialiased（会更细更淡）*/
html, body { -webkit-font-smoothing: auto; text-rendering: optimizeLegibility; }
</style>
"""


def inject():
    st.markdown(_CSS, unsafe_allow_html=True)
