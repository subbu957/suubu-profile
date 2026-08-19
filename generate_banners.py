import os
import math
import numpy as np
from PIL import Image, ImageEnhance, ImageOps, ImageFilter

def process_portrait(image_path, target_w=240, target_h=280):
    """
    Process image with head & shoulders crop, contrast, unsharp mask, and Floyd-Steinberg dithering.
    """
    img = Image.open(image_path).convert('RGB')
    w, h = img.size
    
    # Head and shoulders crop (center-weighted, upper half focus)
    crop_size = min(w, h)
    left = (w - crop_size) // 2
    top = int(h * 0.05) if h > w else 0
    right = left + crop_size
    bottom = top + crop_size
    if bottom > h:
        bottom = h
        top = max(0, bottom - crop_size)
        
    img_cropped = img.crop((left, top, right, bottom))
    img_resized = img_cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    # Grayscale conversion
    gray = img_resized.convert('L')
    
    # 1. Autocontrast cutoff=1
    gray = ImageOps.autocontrast(gray, cutoff=1)
    
    # 2. Contrast approx 1.3x
    enhancer = ImageEnhance.Contrast(gray)
    gray = enhancer.enhance(1.35)
    
    # 3. UnsharpMask radius=3, percent=140
    gray = gray.filter(ImageFilter.UnsharpMask(radius=3, percent=140, threshold=3))
    
    # 4. Serpentine Floyd-Steinberg Dithering
    arr = np.array(gray, dtype=np.float32)
    h_arr, w_arr = arr.shape
    dithered = np.zeros((h_arr, w_arr), dtype=np.uint8)
    
    for y in range(h_arr):
        if y % 2 == 0:
            # Left to right
            x_range = range(w_arr)
            direction = 1
        else:
            # Right to left (serpentine)
            x_range = range(w_arr - 1, -1, -1)
            direction = -1
            
        for x in x_range:
            old_val = arr[y, x]
            new_val = 255 if old_val > 128 else 0
            dithered[y, x] = 1 if new_val == 255 else 0
            err = old_val - new_val
            
            if direction == 1:
                if x + 1 < w_arr:
                    arr[y, x + 1] += err * (7.0 / 16.0)
                if y + 1 < h_arr:
                    if x - 1 >= 0:
                        arr[y + 1, x - 1] += err * (3.0 / 16.0)
                    arr[y + 1, x] += err * (5.0 / 16.0)
                    if x + 1 < w_arr:
                        arr[y + 1, x + 1] += err * (1.0 / 16.0)
            else:
                if x - 1 >= 0:
                    arr[y, x - 1] += err * (7.0 / 16.0)
                if y + 1 < h_arr:
                    if x + 1 < w_arr:
                        arr[y + 1, x + 1] += err * (3.0 / 16.0)
                    arr[y + 1, x] += err * (5.0 / 16.0)
                    if x - 1 >= 0:
                        arr[y + 1, x - 1] += err * (1.0 / 16.0)
                        
    return dithered

def generate_svg_dots(dithered, start_x, start_y, dot_size=1.35, gap=1.55):
    """
    Generate optimized SVG path string for dots, merging contiguous horizontal runs.
    """
    h, w = dithered.shape
    path_groups = [[], [], [], []] # 4 groups for staggered animation
    
    for y in range(h):
        py = start_y + y * gap
        group_idx = (y % 2) * 2 + (y % 4 // 2)
        
        # Find contiguous horizontal runs of 1s
        in_run = False
        run_start = 0
        
        for x in range(w):
            val = dithered[y, x]
            if val == 1:
                if not in_run:
                    in_run = True
                    run_start = x
            else:
                if in_run:
                    in_run = False
                    run_len = x - run_start
                    px = start_x + run_start * gap
                    pw = (run_len - 1) * gap + dot_size
                    path_groups[group_idx].append(f"M{px:.1f},{py:.1f}h{pw:.1f}v{dot_size:.1f}h-{pw:.1f}z")
                    
        if in_run:
            run_len = w - run_start
            px = start_x + run_start * gap
            pw = (run_len - 1) * gap + dot_size
            path_groups[group_idx].append(f"M{px:.1f},{py:.1f}h{pw:.1f}v{dot_size:.1f}h-{pw:.1f}z")
                
    return [" ".join(g) for g in path_groups]

def build_banner_svg(theme="dark", dithered_matrix=None):
    is_dark = theme == "dark"
    
    # Dimensions
    w_total = 1180
    h_total = 610
    
    # Palette
    bg_color = "#0A101F" if is_dark else "#F8FAFC"
    panel_bg = "#0F172A" if is_dark else "#FFFFFF"
    border_color = "#1E293B" if is_dark else "#E2E8F0"
    portrait_color = "#A78BFA" if is_dark else "#7C3AED"
    ui_primary = "#22D3EE" if is_dark else "#0891B2"
    accent_green = "#10B981"
    text_main = "#F1F5F9" if is_dark else "#0F172A"
    text_muted = "#94A3B8" if is_dark else "#64748B"
    text_dim = "#475569" if is_dark else "#94A3B8"
    code_bg = "#070D18" if is_dark else "#F1F5F9"
    grid_line = "#1E293B" if is_dark else "#E2E8F0"
    
    # Generate portrait paths (starting at x=50, y=140)
    portrait_start_x = 50
    portrait_start_y = 150
    dot_size = 1.35
    dot_gap = 1.55
    path_groups = generate_svg_dots(dithered_matrix, portrait_start_x, portrait_start_y, dot_size, dot_gap)
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w_total} {h_total}" width="{w_total}" height="{h_total}">
  <defs>
    <style>
      .mono {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace; }}
      .sans {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
      .dot-leader {{ stroke-dasharray: 2 6; }}
    </style>
    
    <!-- Linear Gradients -->
    <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{ui_primary}" stop-opacity="0.9" />
      <stop offset="100%" stop-color="{portrait_color}" stop-opacity="0.9" />
    </linearGradient>
    
    <linearGradient id="portraitBorderGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{portrait_color}" stop-opacity="0.6" />
      <stop offset="50%" stop-color="{ui_primary}" stop-opacity="0.3" />
      <stop offset="100%" stop-color="{accent_green}" stop-opacity="0.5" />
    </linearGradient>
    
    <linearGradient id="scanGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{portrait_color}" stop-opacity="0" />
      <stop offset="50%" stop-color="{portrait_color}" stop-opacity="0.3" />
      <stop offset="100%" stop-color="{portrait_color}" stop-opacity="0" />
    </linearGradient>
  </defs>

  <!-- Background Canvas -->
  <rect width="{w_total}" height="{h_total}" rx="16" fill="{bg_color}" />
  <rect width="{w_total}" height="{h_total}" rx="16" fill="none" stroke="{border_color}" stroke-width="2" />

  <!-- Terminal Window Header -->
  <rect x="0" y="0" width="{w_total}" height="48" rx="16" fill="{panel_bg}" />
  <path d="M0,36 H{w_total} V48 H0 Z" fill="{panel_bg}" />
  <line x1="0" y1="48" x2="{w_total}" y2="48" stroke="{border_color}" stroke-width="1.5" />

  <!-- Window Controls -->
  <circle cx="28" cy="24" r="6" fill="#EF4444" />
  <circle cx="48" cy="24" r="6" fill="#F59E0B" />
  <circle cx="68" cy="24" r="6" fill="#10B981" />

  <!-- Terminal Command Title -->
  <text x="100" y="29" fill="{text_muted}" class="mono" font-size="13" font-weight="600">~/subbu957/profile.sh --live</text>

  <!-- Top Right Status Badges -->
  <g transform="translate(940, 14)">
    <!-- LIVE Status Pill -->
    <rect x="0" y="0" width="84" height="22" rx="11" fill="{panel_bg}" stroke="{border_color}" stroke-width="1" />
    <circle cx="14" cy="11" r="4.5" fill="{accent_green}">
      <animate attributeName="opacity" values="1;0.2;1" dur="2s" repeatCount="indefinite" />
    </circle>
    <text x="26" y="15" fill="{accent_green}" class="mono" font-size="11" font-weight="700" letter-spacing="1">LIVE</text>
    
    <!-- Handle Pill -->
    <rect x="94" y="0" width="124" height="22" rx="11" fill="{code_bg}" stroke="{ui_primary}" stroke-opacity="0.4" stroke-width="1" />
    <text x="106" y="15" fill="{ui_primary}" class="mono" font-size="11" font-weight="600">@subbu957</text>
  </g>

  <!-- ==================== LEFT PANEL (VISUAL.MAP / PORTRAIT) ==================== -->
  <g transform="translate(24, 66)">
    <!-- Panel Container -->
    <rect x="0" y="0" width="410" height="520" rx="12" fill="{panel_bg}" stroke="{border_color}" stroke-width="1.5" />
    
    <!-- Header Bar -->
    <rect x="0" y="0" width="410" height="34" rx="12" fill="{code_bg}" />
    <path d="M0,24 H410 V34 H0 Z" fill="{code_bg}" />
    <line x1="0" y1="34" x2="410" y2="34" stroke="{border_color}" stroke-width="1" />
    
    <!-- Label -->
    <text x="16" y="22" fill="{ui_primary}" class="mono" font-size="11" font-weight="700" letter-spacing="1.5">VISUAL.MAP // PORTRAIT_MATRIX</text>
    <text x="320" y="22" fill="{text_dim}" class="mono" font-size="10">300x340.FS</text>

    <!-- Portrait Frame -->
    <rect x="18" y="48" width="374" height="438" rx="8" fill="{code_bg}" stroke="url(#portraitBorderGrad)" stroke-width="1.5" />
    
    <!-- Radar Sweep Scan Effect -->
    <rect x="19" y="49" width="372" height="50" fill="url(#scanGrad)" pointer-events="none">
      <animate attributeName="y" values="49;420;49" dur="7s" repeatCount="indefinite" />
    </rect>

    <!-- Dithered Portrait Dot Layers (Shape Rendering CrispEdges) -->
    <g shape-rendering="crispEdges" fill="{portrait_color}">
      <path d="{path_groups[0]}">
        <animate attributeName="opacity" values="0;1" dur="0.8s" begin="0.1s" fill="freeze" />
      </path>
      <path d="{path_groups[1]}">
        <animate attributeName="opacity" values="0;1" dur="1.0s" begin="0.3s" fill="freeze" />
      </path>
      <path d="{path_groups[2]}">
        <animate attributeName="opacity" values="0;1" dur="1.2s" begin="0.5s" fill="freeze" />
      </path>
      <path d="{path_groups[3]}">
        <animate attributeName="opacity" values="0;1" dur="1.4s" begin="0.7s" fill="freeze" />
      </path>
    </g>

    <!-- Portrait Status Footer -->
    <g transform="translate(18, 494)">
      <text x="6" y="16" fill="{text_muted}" class="mono" font-size="10">AUTH: VERIFIED_DEV</text>
      <text x="260" y="16" fill="{accent_green}" class="mono" font-size="10" font-weight="600">STATE: ACTIVE</text>
    </g>
  </g>

  <!-- ==================== RIGHT PANEL (SYSTEM.INFO) ==================== -->
  <g transform="translate(450, 66)">
    <!-- Panel Container -->
    <rect x="0" y="0" width="706" height="520" rx="12" fill="{panel_bg}" stroke="{border_color}" stroke-width="1.5" />

    <!-- Header Bar -->
    <rect x="0" y="0" width="706" height="34" rx="12" fill="{code_bg}" />
    <path d="M0,24 H706 V34 H0 Z" fill="{code_bg}" />
    <line x1="0" y1="34" x2="706" y2="34" stroke="{border_color}" stroke-width="1" />
    
    <!-- Title -->
    <text x="18" y="22" fill="{ui_primary}" class="mono" font-size="11" font-weight="700" letter-spacing="1.5">SYSTEM.INFO // DEVELOPER_TELEMETRY</text>
    <text x="590" y="22" fill="{text_dim}" class="mono" font-size="10">SYS_REV: 2.0</text>

    <!-- Developer Name & Hero Title -->
    <g transform="translate(24, 60)">
      <text x="0" y="26" fill="{text_main}" class="sans" font-size="26" font-weight="800" letter-spacing="-0.5">B.V.S. Subrahmanyam</text>
      <text x="0" y="50" fill="{ui_primary}" class="mono" font-size="13" font-weight="600">AI &amp; ML Student • Full-Stack Web Developer</text>
    </g>

    <!-- Horizontal Divider -->
    <line x1="24" y1="126" x2="682" y2="126" stroke="{border_color}" stroke-width="1" />

    <!-- Telemetry Information Rows with Dotted Leaders -->
    <g transform="translate(24, 150)" class="mono" font-size="12">
      <!-- Row 1: Origin -->
      <g transform="translate(0, 0)">
        <text x="0" y="12" fill="{text_muted}" font-weight="600">Origin</text>
        <line x1="60" y1="9" x2="230" y2="9" stroke="{text_dim}" stroke-width="1.5" class="dot-leader" />
        <text x="240" y="12" fill="{text_main}" font-weight="500">Andhra Pradesh, India 🇮🇳</text>
      </g>

      <!-- Row 2: Education -->
      <g transform="translate(0, 26)">
        <text x="0" y="12" fill="{text_muted}" font-weight="600">Education</text>
        <line x1="80" y1="9" x2="230" y2="9" stroke="{text_dim}" stroke-width="1.5" class="dot-leader" />
        <text x="240" y="12" fill="{text_main}" font-weight="500">B.Tech — Artificial Intelligence &amp; ML</text>
      </g>

      <!-- Row 3: Status -->
      <g transform="translate(0, 52)">
        <text x="0" y="12" fill="{text_muted}" font-weight="600">Status</text>
        <line x1="60" y1="9" x2="230" y2="9" stroke="{text_dim}" stroke-width="1.5" class="dot-leader" />
        <text x="240" y="12" fill="{accent_green}" font-weight="600">Building • Learning • Shipping</text>
      </g>

      <!-- Row 4: Core.Lang -->
      <g transform="translate(0, 78)">
        <text x="0" y="12" fill="{text_muted}" font-weight="600">Core.Lang</text>
        <line x1="80" y1="9" x2="230" y2="9" stroke="{text_dim}" stroke-width="1.5" class="dot-leader" />
        <text x="240" y="12" fill="{text_main}" font-weight="500">Python • Java • JavaScript • C</text>
      </g>

      <!-- Row 5: Core.Frontend -->
      <g transform="translate(0, 104)">
        <text x="0" y="12" fill="{text_muted}" font-weight="600">Core.Frontend</text>
        <line x1="115" y1="9" x2="230" y2="9" stroke="{text_dim}" stroke-width="1.5" class="dot-leader" />
        <text x="240" y="12" fill="{text_main}" font-weight="500">HTML5 • CSS3 • JavaScript • React.js</text>
      </g>

      <!-- Row 6: Core.Backend -->
      <g transform="translate(0, 130)">
        <text x="0" y="12" fill="{text_muted}" font-weight="600">Core.Backend</text>
        <line x1="110" y1="9" x2="230" y2="9" stroke="{text_dim}" stroke-width="1.5" class="dot-leader" />
        <text x="240" y="12" fill="{text_main}" font-weight="500">Node.js • Express.js</text>
      </g>

      <!-- Row 7: Core.Database -->
      <g transform="translate(0, 156)">
        <text x="0" y="12" fill="{text_muted}" font-weight="600">Core.Database</text>
        <line x1="120" y1="9" x2="230" y2="9" stroke="{text_dim}" stroke-width="1.5" class="dot-leader" />
        <text x="240" y="12" fill="{text_main}" font-weight="500">SQL • MongoDB</text>
      </g>

      <!-- Row 8: Core.AI -->
      <g transform="translate(0, 182)">
        <text x="0" y="12" fill="{text_muted}" font-weight="600">Core.AI</text>
        <line x1="68" y1="9" x2="230" y2="9" stroke="{text_dim}" stroke-width="1.5" class="dot-leader" />
        <text x="240" y="12" fill="{portrait_color}" font-weight="600">Machine Learning • Computer Vision</text>
      </g>

      <!-- Row 9: ToolChain -->
      <g transform="translate(0, 208)">
        <text x="0" y="12" fill="{text_muted}" font-weight="600">ToolChain</text>
        <line x1="84" y1="9" x2="230" y2="9" stroke="{text_dim}" stroke-width="1.5" class="dot-leader" />
        <text x="240" y="12" fill="{text_main}" font-weight="500">VS Code • Git • GitHub</text>
      </g>

      <!-- Row 10: Grid.Mail -->
      <g transform="translate(0, 234)">
        <text x="0" y="12" fill="{text_muted}" font-weight="600">Grid.Mail</text>
        <line x1="80" y1="9" x2="230" y2="9" stroke="{text_dim}" stroke-width="1.5" class="dot-leader" />
        <text x="240" y="12" fill="{ui_primary}" font-weight="500">bvssubbu2005@gmail.com</text>
      </g>

      <!-- Row 11: Grid.LinkedIn -->
      <g transform="translate(0, 260)">
        <text x="0" y="12" fill="{text_muted}" font-weight="600">Grid.LinkedIn</text>
        <line x1="110" y1="9" x2="230" y2="9" stroke="{text_dim}" stroke-width="1.5" class="dot-leader" />
        <text x="240" y="12" fill="{ui_primary}" font-weight="500">linkedin.com/in/subrhamanyam-bhattaram-658656303</text>
      </g>

      <!-- Row 12: Grid.GitHub -->
      <g transform="translate(0, 286)">
        <text x="0" y="12" fill="{text_muted}" font-weight="600">Grid.GitHub</text>
        <line x1="95" y1="9" x2="230" y2="9" stroke="{text_dim}" stroke-width="1.5" class="dot-leader" />
        <text x="240" y="12" fill="{ui_primary}" font-weight="500">github.com/subbu957</text>
      </g>
    </g>

    <!-- Bottom Status Bar -->
    <g transform="translate(24, 476)">
      <rect x="0" y="0" width="658" height="28" rx="6" fill="{code_bg}" stroke="{border_color}" stroke-width="1" />
      <text x="12" y="18" fill="{text_dim}" class="mono" font-size="10">KERNEL: READY</text>
      <text x="230" y="18" fill="{text_dim}" class="mono" font-size="10">FOCUS: AI/ML &amp; FULL-STACK</text>
      <text x="530" y="18" fill="{accent_green}" class="mono" font-size="10" font-weight="600">ALL SYSTEMS GO</text>
    </g>
  </g>
</svg>
'''
    return svg

def main():
    os.makedirs("profile/assets", exist_ok=True)
    
    print("Processing portrait matrix...")
    # target_w=240, target_h=280 gives clean, sharp dot representation matching 374x438 frame
    dithered = process_portrait("profile/photo.png", target_w=236, target_h=276)
    
    print("Generating dark.svg...")
    dark_svg = build_banner_svg(theme="dark", dithered_matrix=dithered)
    with open("profile/assets/dark.svg", "w", encoding="utf-8") as f:
        f.write(dark_svg)
        
    print("Generating light.svg...")
    light_svg = build_banner_svg(theme="light", dithered_matrix=dithered)
    with open("profile/assets/light.svg", "w", encoding="utf-8") as f:
        f.write(light_svg)
        
    dark_size_kb = os.path.getsize("profile/assets/dark.svg") / 1024
    light_size_kb = os.path.getsize("profile/assets/light.svg") / 1024
    
    print(f"dark.svg size: {dark_size_kb:.2f} KB")
    print(f"light.svg size: {light_size_kb:.2f} KB")

if __name__ == "__main__":
    main()
