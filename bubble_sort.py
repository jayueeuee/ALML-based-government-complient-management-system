# print("hii")

# a = [3,4,2,1,5]
# print(len(a))
# for i in range(0,len(a)):
#     for j in range(0,len(a)-i-1):
#         if ( a[j] > a [j+1 ]):
#             a[j] , a[j+1] = a[j+1] , a[j]


# print(a)
import matplotlib.patches as patches
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(16, 9), dpi=300)
ax.set_xlim(0, 16)
ax.set_ylim(0, 9)
ax.axis("off")

# Title Header
ax.add_patch(
    patches.FancyBboxPatch(
        (3, 8.0),
        10,
        0.8,
        boxstyle="round,pad=0.2",
        ec="#154360",
        fc="#154360",
        lw=2,
    )
)
ax.text(
    8,
    8.4,
    "AI Governance Complaint Management System",
    color="white",
    fontsize=16,
    weight="bold",
    ha="center",
)
ax.text(
    8,
    8.15,
    "From Citizen to Resolution – Powered by Hugging Face ViLT & NLP",
    color="#AED6F1",
    fontsize=10,
    ha="center",
)


# Helper function to create boxed stages
def add_card(x, y, w, h, title, lines, bg_color, border_color):
  ax.add_patch(
      patches.FancyBboxPatch(
          (x, y),
          w,
          h,
          boxstyle="round,pad=0.15",
          ec=border_color,
          fc=bg_color,
          lw=1.5,
      )
  )
  ax.text(
      x + w / 2,
      y + h - 0.35,
      title,
      fontsize=11,
      weight="bold",
      ha="center",
      color="#1B2631",
  )
  line_y = y + h - 0.7
  for line in lines:
    ax.text(
        x + 0.15, line_y, line, fontsize=8.5, color="#2C3E50", va="top"
    )
    line_y -= 0.3


# 1. Citizen Portal
add_card(
    0.5,
    4.5,
    2.4,
    3.0,
    "1. Citizen Portal",
    [
        "• User signs in",
        "• Enter text complaint",
        "• Upload photo evidence",
        "• Mobile / Web input",
    ],
    "#EBF5FB",
    "#2980B9",
)

# 2. AI Processing
add_card(
    3.3,
    4.5,
    3.2,
    3.0,
    "2. AI Processing Engine",
    [
        "NLP (Scikit-Learn):",
        " • Category: category_model.pkl",
        " • Priority: priority_model.pkl",
        "",
        "Multimodal VQA (Hugging Face):",
        " • Model: ViLT-b32-finetuned-vqa",
        " • Dynamic question generation",
    ],
    "#F4ECF7",
    "#8E44AD",
)

# 3. Verification Gateway
ax.add_patch(
    patches.FancyBboxPatch(
        (7.0, 4.5),
        2.8,
        3.0,
        boxstyle="round,pad=0.15",
        ec="#27AE60",
        fc="#EAFAF1",
        lw=1.5,
    )
)
ax.text(
    8.4,
    7.15,
    "3. Verification Gateway",
    fontsize=11,
    weight="bold",
    ha="center",
    color="#1B2631",
)
ax.text(
    8.4,
    6.6,
    "VQA Match Claim?",
    fontsize=9.5,
    weight="bold",
    ha="center",
    color="#2C3E50",
)

# Verified & Suspicious boxes
ax.add_patch(
    patches.FancyBboxPatch(
        (7.2, 5.7),
        2.4,
        0.55,
        boxstyle="round,pad=0.1",
        ec="#27AE60",
        fc="#D5F5E3",
        lw=1.2,
    )
)
ax.text(
    8.4,
    5.95,
    "✔ Verified (Direct Routing)",
    fontsize=8.5,
    weight="bold",
    color="#196F3D",
    ha="center",
)

ax.add_patch(
    patches.FancyBboxPatch(
        (7.2, 4.7),
        2.4,
        0.65,
        boxstyle="round,pad=0.1",
        ec="#C0392B",
        fc="#FDEDEC",
        lw=1.2,
    )
)
ax.text(
    8.4,
    5.15,
    "✖ Suspicious Claim",
    fontsize=8.5,
    weight="bold",
    color="#922B21",
    ha="center",
)
ax.text(
    8.4,
    4.85,
    "Image mismatch detected",
    fontsize=7.5,
    color="#922B21",
    ha="center",
)

# 3B. Physical Spot Verification
add_card(
    10.3,
    4.5,
    2.5,
    3.0,
    "3B. Spot Review",
    [
        "Field Officer Dispatch:",
        " • Assigned to inspect spot",
        " • Physical ground verification",
        " • Confirms or drops ticket",
    ],
    "#FFF9E6",
    "#F39C12",
)

# 4. Routing & Assignment
add_card(
    0.5,
    2.1,
    4.5,
    1.9,
    "4. Routing & Assignment",
    [
        "• Categorized Department (Road / Pothole, Water)",
        "• Severity Tier (High / Medium / Low)",
        "• Auto-assigned to Ward Officer / Nagar Sevak",
    ],
    "#E8F8F5",
    "#16A085",
)

# 5. Authority Dashboard
add_card(
    5.5,
    2.1,
    4.5,
    1.9,
    "5. Authority Dashboard (Nagar Sevak)",
    [
        "• Access authenticated complaints",
        "• Inspect site evidence and location",
        "• Update workflow status to Resolved",
    ],
    "#FEF9E7",
    "#D4AC0D",
)

# 6. Admin Oversight
add_card(
    10.5,
    2.1,
    5.0,
    1.9,
    "6. Admin Oversight & Analytics",
    [
        "• Folium Map: SLA Breaches & Black Zones",
        "• Plotly: Department performance analytics",
        "• Audit trail of Verified vs. Rejected tickets",
    ],
    "#F5EEF8",
    "#7D3C98",
)

# Connectors
arrow_style = dict(arrowstyle="->", lw=2, color="#34495E")
ax.annotate("", xy=(3.3, 6.0), xytext=(2.9, 6.0), arrowprops=arrow_style)
ax.annotate("", xy=(7.0, 6.0), xytext=(6.5, 6.0), arrowprops=arrow_style)
ax.annotate("", xy=(10.3, 5.0), xytext=(9.6, 5.0), arrowprops=arrow_style)

# Arrows to bottom row
ax.annotate(
    "",
    xy=(2.7, 4.0),
    xytext=(7.2, 5.95),
    arrowprops=dict(arrowstyle="->", lw=1.5, color="#27AE60"),
)
ax.annotate(
    "",
    xy=(4.5, 4.0),
    xytext=(11.5, 4.5),
    arrowprops=dict(arrowstyle="->", lw=1.5, color="#F39C12"),
)
ax.annotate("", xy=(5.5, 3.0), xytext=(5.0, 3.0), arrowprops=arrow_style)
ax.annotate("", xy=(10.5, 3.0), xytext=(10.0, 3.0), arrowprops=arrow_style)

# Bottom Tech Stack Banner
ax.add_patch(
    patches.FancyBboxPatch(
        (0.5, 0.4),
        15.0,
        1.2,
        boxstyle="round,pad=0.15",
        ec="#BDC3C7",
        fc="#F8F9F9",
        lw=1.5,
    )
)
ax.text(
    1.5,
    1.1,
    "Technology Stack",
    fontsize=12,
    weight="bold",
    color="#2C3E50",
    va="center",
)
ax.text(
    4.0,
    1.2,
    "UI: Streamlit & Plotly",
    fontsize=9,
    weight="bold",
    color="#2C3E50",
)
ax.text(
    4.0,
    0.7,
    "Backend: Python 3 & MySQL",
    fontsize=8.5,
    color="#566573",
)
ax.text(
    8.0,
    1.2,
    "AI Models: Scikit-Learn NLP",
    fontsize=9,
    weight="bold",
    color="#2C3E50",
)
ax.text(
    8.0,
    0.7,
    "Vision: Hugging Face ViLT (PyTorch)",
    fontsize=8.5,
    color="#566573",
)
ax.text(
    12.5,
    1.2,
    "Spatial: Folium & GeoPandas",
    fontsize=9,
    weight="bold",
    color="#2C3E50",
)
ax.text(
    12.5,
    0.7,
    "Cloud: Streamlit Deployment",
    fontsize=8.5,
    color="#566573",
)

plt.tight_layout()
plt.savefig("ai_governance_architecture.png", dpi=300)
print("Image saved successfully as 'ai_governance_architecture.png'")