import os
from PIL import Image, ImageEnhance, ImageOps
import numpy as np

def generate_matrix_code_art(image_path="profile/photo.png", width=80, height=48):
    """
    Generate high-density matrix code art from user portrait using developer syntax & building blocks.
    """
    img = Image.open(image_path).convert('L')
    w, h = img.size
    crop_size = min(w, h)
    left = (w - crop_size) // 2
    top = int(h * 0.05) if h > w else 0
    img_cropped = img.crop((left, top, left + crop_size, top + crop_size))
    img_resized = img_cropped.resize((width, height), Image.Resampling.LANCZOS)
    
    # Enhance contrast
    img_enhanced = ImageEnhance.Contrast(ImageOps.autocontrast(img_resized)).enhance(1.4)
    arr = np.array(img_enhanced)
    
    # Density ramp using code characters and building blocks
    # Dark to light
    code_tokens = [" ", ".", ":", "-", "+", "=", "*", "#", "%", "@", "█"]
    block_tokens = [" ", "░", "▒", "▓", "█"]
    matrix_tokens = [" ", "0", "1", "<", "/", ">", "{", "}", "[", "]", "λ", "π", "█"]
    
    lines = []
    for row in arr:
        line_chars = []
        for val in row:
            idx = int((val / 255.0) * (len(matrix_tokens) - 1))
            line_chars.append(matrix_tokens[idx])
        lines.append("".join(line_chars))
        
    return "\n".join(lines)

def generate_interactive_html(image_path="profile/photo.png"):
    """
    Generate an interactive, creative HTML/JS building blocks & matrix portrait viewer.
    Clicking breaks the portrait into floating/falling 3D building blocks that magnetically snap back!
    """
    img = Image.open(image_path).convert('L')
    w, h = img.size
    crop_size = min(w, h)
    left = (w - crop_size) // 2
    top = int(h * 0.05)
    img_cropped = img.crop((left, top, left + crop_size, top + crop_size))
    
    # 60x60 grid of interactive blocks
    grid_w, grid_h = 64, 64
    img_resized = img_cropped.resize((grid_w, grid_h), Image.Resampling.LANCZOS)
    img_enhanced = ImageEnhance.Contrast(ImageOps.autocontrast(img_resized)).enhance(1.5)
    arr = np.array(img_enhanced)
    
    pixel_data = []
    for y in range(grid_h):
        for x in range(grid_w):
            brightness = int(arr[y, x])
            if brightness > 30: # Filter dark background
                pixel_data.append([x, y, brightness])
                
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>B.V.S. Subrahmanyam — Interactive Matrix Code Portrait</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      background: #0A101F;
      color: #F1F5F9;
      font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
    }}
    
    #header {{
      position: absolute;
      top: 20px;
      text-align: center;
      z-index: 10;
      pointer-events: none;
    }}
    
    h1 {{
      font-size: 1.4rem;
      color: #22D3EE;
      letter-spacing: 2px;
      text-transform: uppercase;
    }}
    
    p {{
      font-size: 0.85rem;
      color: #94A3B8;
      margin-top: 6px;
    }}
    
    .badge {{
      display: inline-block;
      margin-top: 8px;
      padding: 4px 12px;
      background: rgba(34, 211, 238, 0.1);
      border: 1px solid rgba(34, 211, 238, 0.3);
      border-radius: 999px;
      color: #10B981;
      font-size: 0.75rem;
      font-weight: bold;
    }}
    
    canvas {{
      display: block;
      cursor: crosshair;
    }}
    
    #controls {{
      position: absolute;
      bottom: 24px;
      display: flex;
      gap: 12px;
      z-index: 10;
    }}
    
    button {{
      background: #0F172A;
      color: #22D3EE;
      border: 1px solid #1E293B;
      padding: 8px 16px;
      border-radius: 8px;
      font-family: inherit;
      font-size: 0.8rem;
      cursor: pointer;
      transition: all 0.2s;
    }}
    
    button:hover {{
      background: #1E293B;
      border-color: #22D3EE;
      box-shadow: 0 0 12px rgba(34, 211, 238, 0.4);
      transform: translateY(-2px);
    }}
  </style>
</head>
<body>
  <div id="header">
    <h1>B.V.S. Subrahmanyam // Matrix Visual Map</h1>
    <p>Click or drag anywhere to blast code building blocks • Watch them assemble</p>
    <div class="badge">● INTERACTIVE VOXEL MATRIX</div>
  </div>

  <canvas id="matrixCanvas"></canvas>

  <div id="controls">
    <button onclick="explodeAll()">💥 Scatter Building Blocks</button>
    <button onclick="toggleMode()">🔄 Toggle Code / Voxels</button>
    <button onclick="assembleAll()">🧲 Assemble Portrait</button>
  </div>

  <script>
    const rawPixels = {pixel_data};
    const canvas = document.getElementById('matrixCanvas');
    const ctx = canvas.getContext('2d');
    
    let width, height;
    function resize() {{
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    }}
    window.addEventListener('resize', resize);
    resize();

    const CODE_CHARS = ['0', '1', 'AI', 'ML', 'def', 'const', '{{}}', '=>', 'import', 'py', 'react', 'git', 'sql'];
    let showCode = true;

    class BuildingBlock {{
      constructor(gx, gy, brightness) {{
        this.gx = gx;
        this.gy = gy;
        this.brightness = brightness;
        this.char = CODE_CHARS[(gx + gy) % CODE_CHARS.length];
        
        // Target home position
        this.updateHome();
        
        // Current animated position
        this.x = this.homeX + (Math.random() - 0.5) * 600;
        this.y = this.homeY + (Math.random() - 0.5) * 600;
        this.vx = 0;
        this.vy = 0;
        
        // Visual properties
        this.size = 8;
        const norm = brightness / 255;
        this.color = `rgba(167, 139, 250, ${{0.3 + norm * 0.7}})`; // Purple hue
        this.accentColor = `rgba(34, 211, 238, ${{0.4 + norm * 0.6}})`; // Cyan
      }}

      updateHome() {{
        const scale = Math.min(width, height) * 0.65 / 64;
        const offsetX = (width - 64 * scale) / 2;
        const offsetY = (height - 64 * scale) / 2 + 10;
        this.homeX = offsetX + this.gx * scale;
        this.homeY = offsetY + this.gy * scale;
        this.currentScale = scale;
      }}

      update(mouseX, mouseY, isMouseDown) {{
        // Spring physics towards home position
        const dx = this.homeX - this.x;
        const dy = this.homeY - this.y;
        this.vx += dx * 0.05;
        this.vy += dy * 0.05;
        
        // Friction
        this.vx *= 0.88;
        this.vy *= 0.88;

        // Mouse interaction (blast force)
        if (mouseX !== undefined) {{
          const mdx = this.x - mouseX;
          const mdy = this.y - mouseY;
          const dist = Math.sqrt(mdx * mdx + mdy * mdy);
          const maxDist = isMouseDown ? 180 : 90;
          if (dist < maxDist && dist > 0) {{
            const force = (maxDist - dist) / maxDist;
            const power = isMouseDown ? 25 : 8;
            this.vx += (mdx / dist) * force * power;
            this.vy += (mdy / dist) * force * power;
          }}
        }}

        this.x += this.vx;
        this.y += this.vy;
      }}

      draw() {{
        const norm = this.brightness / 255;
        if (showCode) {{
          ctx.font = `${{Math.max(8, this.currentScale * 0.95)}}px ui-monospace, monospace`;
          ctx.fillStyle = norm > 0.7 ? this.accentColor : this.color;
          ctx.fillText(this.char, this.x, this.y);
        }} else {{
          // Building block / Voxel style
          const bSize = this.currentScale * 0.85;
          ctx.fillStyle = norm > 0.7 ? '#22D3EE' : (norm > 0.4 ? '#A78BFA' : '#1E293B');
          ctx.fillRect(this.x, this.y, bSize, bSize);
          ctx.strokeStyle = '#0A101F';
          ctx.strokeRect(this.x, this.y, bSize, bSize);
        }}
      }}
    }}

    const blocks = rawPixels.map(([gx, gy, b]) => new BuildingBlock(gx, gy, b));

    let mouse = {{ x: -999, y: -999, isDown: false }};

    window.addEventListener('mousemove', (e) => {{
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    }});

    window.addEventListener('mousedown', (e) => {{
      mouse.isDown = true;
    }});

    window.addEventListener('mouseup', () => {{
      mouse.isDown = false;
    }});

    window.addEventListener('resize', () => {{
      blocks.forEach(b => b.updateHome());
    }});

    function explodeAll() {{
      blocks.forEach(b => {{
        b.vx = (Math.random() - 0.5) * 60;
        b.vy = (Math.random() - 0.5) * 60;
      }});
    }}

    function assembleAll() {{
      blocks.forEach(b => {{
        b.x = b.homeX + (Math.random() - 0.5) * 20;
        b.y = b.homeY + (Math.random() - 0.5) * 20;
        b.vx = 0;
        b.vy = 0;
      }});
    }}

    function toggleMode() {{
      showCode = !showCode;
    }}

    // Matrix Rain background effect
    const matrixCols = Math.floor(window.innerWidth / 20);
    const drops = Array(matrixCols).fill(1);

    function drawMatrixRain() {{
      ctx.fillStyle = 'rgba(10, 16, 31, 0.2)';
      ctx.fillRect(0, 0, width, height);

      ctx.fillStyle = '#064e3b';
      ctx.font = '12px monospace';
      for (let i = 0; i < drops.length; i++) {{
        const text = String.fromCharCode(0x30A0 + Math.random() * 32);
        const x = i * 20;
        const y = drops[i] * 20;
        ctx.fillText(text, x, y);
        if (y > height && Math.random() > 0.975) {{
          drops[i] = 0;
        }}
        drops[i]++;
      }}
    }}

    function animate() {{
      drawMatrixRain();
      
      blocks.forEach(b => {{
        b.update(mouse.x, mouse.y, mouse.isDown);
        b.draw();
      }});
      
      requestAnimationFrame(animate);
    }}

    animate();
  </script>
</body>
</html>
"""
    return html_content

def main():
    print("Generating ASCII Matrix Code block...")
    code_art = generate_matrix_code_art("profile/photo.png", width=74, height=44)
    with open("profile/matrix_portrait.txt", "w", encoding="utf-8") as f:
        f.write(code_art)
    print("Saved profile/matrix_portrait.txt")
    
    print("Generating interactive matrix HTML canvas app...")
    html = generate_interactive_html("profile/photo.png")
    with open("profile/matrix_portrait.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved profile/matrix_portrait.html")

if __name__ == "__main__":
    main()
